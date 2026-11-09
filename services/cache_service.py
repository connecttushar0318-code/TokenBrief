import json
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from config import settings
from models import SemanticQueryCacheRecord

class SemanticQueryCacheService:
    @staticmethod
    async def get_cached_answer(
        database_session: AsyncSession,
        query_vector: List[float],
        filter_document_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        if filter_document_id is None:
            return None

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

        return {
            "cached_query": matched_row.query_text,
            "answer": matched_row.cached_answer,
            "sources": parsed_sources,
            "similarity": round(similarity * 100.0, 2),
            "hit_count": matched_row.hit_count + 1
        }

    @staticmethod
    async def store_query_cache(
        database_session: AsyncSession,
        query_text: str,
        query_vector: List[float],
        answer_text: str,
        sources: List[Dict[str, Any]],
        document_id: Optional[int] = None
    ):
        if document_id is None:
            return

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
