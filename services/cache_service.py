import json
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from config import settings
from models import SemanticQueryCacheRecord


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    return sum(a * b for a, b in zip(vec_a, vec_b))


class SemanticQueryCacheService:
    # Lightweight process-local L1 semantic cache to eliminate DB roundtrips on repeat queries
    _L1_CACHE: Dict[int, List[Dict[str, Any]]] = {}
    _MAX_ENTRIES_PER_DOC = 25
    _MAX_DOCS = 50

    @classmethod
    def clear_memory_cache(cls, document_id: Optional[int] = None) -> None:
        if document_id is None:
            cls._L1_CACHE.clear()
        else:
            cls._L1_CACHE.pop(document_id, None)

    @classmethod
    def _save_to_l1(
        cls,
        document_id: int,
        query_text: str,
        query_vector: List[float],
        answer_text: str,
        sources: List[Dict[str, Any]],
        hit_count: int = 1,
        record_id: Optional[int] = None,
    ) -> None:
        if len(cls._L1_CACHE) >= cls._MAX_DOCS and document_id not in cls._L1_CACHE:
            oldest_key = next(iter(cls._L1_CACHE))
            cls._L1_CACHE.pop(oldest_key, None)

        entries = cls._L1_CACHE.setdefault(document_id, [])
        entries.append({
            "id": record_id,
            "query_text": query_text,
            "vector": query_vector,
            "answer": answer_text,
            "sources": sources,
            "hit_count": hit_count,
        })
        if len(entries) > cls._MAX_ENTRIES_PER_DOC:
            entries.pop(0)

    @classmethod
    async def get_cached_answer(
        cls,
        database_session: AsyncSession,
        query_vector: List[float],
        filter_document_id: Optional[int] = None,
        defer_hit_update: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if filter_document_id is None:
            return None

        # 1. Check fast in-memory L1 cache first (< 0.1 ms, zero DB queries)
        l1_entries = cls._L1_CACHE.get(filter_document_id)
        if l1_entries:
            best_entry = None
            best_sim = -1.0
            for entry in l1_entries:
                sim = _cosine_similarity(query_vector, entry["vector"])
                if sim > best_sim:
                    best_sim = sim
                    best_entry = entry
            if best_entry and best_sim >= settings.semantic_cache_similarity_threshold:
                best_entry["hit_count"] += 1
                return {
                    "record_id": best_entry.get("id"),
                    "cached_query": best_entry["query_text"],
                    "answer": best_entry["answer"],
                    "sources": best_entry["sources"],
                    "similarity": round(best_sim * 100.0, 2),
                    "hit_count": best_entry["hit_count"],
                }

        # 2. Fallback to PostgreSQL pgvector L2 cache
        distance_col = SemanticQueryCacheRecord.embedding_vector.cosine_distance(
            query_vector
        ).label("distance")

        stmt = select(
            SemanticQueryCacheRecord.id,
            SemanticQueryCacheRecord.query_text,
            SemanticQueryCacheRecord.cached_answer,
            SemanticQueryCacheRecord.cached_sources_json,
            SemanticQueryCacheRecord.hit_count,
            distance_col
        )
        stmt = stmt.where(SemanticQueryCacheRecord.document_id == filter_document_id)
        stmt = stmt.order_by(distance_col).limit(1)

        result = await database_session.execute(stmt)
        matched_row = result.first()
        if not matched_row:
            return None

        distance = float(matched_row.distance) if matched_row.distance is not None else 1.0
        similarity = 1.0 - distance

        if similarity < settings.semantic_cache_similarity_threshold:
            return None

        if not defer_hit_update:
            update_stmt = (
                update(SemanticQueryCacheRecord)
                .where(SemanticQueryCacheRecord.id == matched_row.id)
                .values(hit_count=SemanticQueryCacheRecord.hit_count + 1)
            )
            await database_session.execute(update_stmt)
            await database_session.commit()

        try:
            parsed_sources = json.loads(matched_row.cached_sources_json)
        except Exception:
            parsed_sources = []

        cls._save_to_l1(
            document_id=filter_document_id,
            query_text=matched_row.query_text,
            query_vector=query_vector,
            answer_text=matched_row.cached_answer,
            sources=parsed_sources,
            hit_count=matched_row.hit_count + 1,
            record_id=matched_row.id,
        )

        return {
            "record_id": matched_row.id,
            "cached_query": matched_row.query_text,
            "answer": matched_row.cached_answer,
            "sources": parsed_sources,
            "similarity": round(similarity * 100.0, 2),
            "hit_count": matched_row.hit_count + 1
        }

    @classmethod
    async def increment_hit_count(cls, database_session: AsyncSession, record_id: int) -> None:
        try:
            update_stmt = (
                update(SemanticQueryCacheRecord)
                .where(SemanticQueryCacheRecord.id == record_id)
                .values(hit_count=SemanticQueryCacheRecord.hit_count + 1)
            )
            await database_session.execute(update_stmt)
            await database_session.commit()
        except Exception:
            await database_session.rollback()

    @classmethod
    async def store_query_cache(
        cls,
        database_session: AsyncSession,
        query_text: str,
        query_vector: List[float],
        answer_text: str,
        sources: List[Dict[str, Any]],
        document_id: Optional[int] = None
    ):
        if document_id is None:
            return

        cls._save_to_l1(
            document_id=document_id,
            query_text=query_text,
            query_vector=query_vector,
            answer_text=answer_text,
            sources=sources,
            hit_count=1,
        )

        try:
            cache_record = SemanticQueryCacheRecord(
                document_id=document_id,
                query_text=query_text,
                embedding_vector=query_vector,
                cached_answer=answer_text,
                cached_sources_json=json.dumps(sources),
                hit_count=1
            )
            database_session.add(cache_record)
            await database_session.commit()
        except Exception:
            await database_session.rollback()
