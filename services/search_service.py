import math
import re
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from models import DocumentChunkRecord, DocumentRecord
from services.embedding_service import VectorEmbeddingGenerator
from services.rerank_service import CandidateRerankerService

class VectorSimilaritySearchEngine:

    @classmethod
    async def find_most_relevant_chunks(
        cls,
        database_session: AsyncSession,
        user_query_text: str,
        filter_document_id: Optional[int] = None,
        filter_user_id: Optional[int] = None,
        maximum_results_count: int = 4
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        query_vector = await asyncio.to_thread(
            VectorEmbeddingGenerator.generate_single_embedding,
            user_query_text
        )

        vector_ranked_candidates = await cls._execute_vector_search(
            database_session=database_session,
            query_vector=query_vector,
            filter_document_id=filter_document_id,
            filter_user_id=filter_user_id,
            limit=25
        )

        lexical_ranked_candidates = await cls._execute_lexical_search(
            database_session=database_session,
            user_query_text=user_query_text,
            filter_document_id=filter_document_id,
            filter_user_id=filter_user_id,
            limit=25
        )

        fused_candidates = cls._reciprocal_rank_fusion(
            vector_candidates=vector_ranked_candidates,
            lexical_candidates=lexical_ranked_candidates,
            rrf_k=60,
            top_n=15
        )

        reranked_chunks = CandidateRerankerService.rerank_chunks(
            query_text=user_query_text,
            retrieved_chunks=fused_candidates,
            top_k=maximum_results_count
        )

        return reranked_chunks, query_vector

    @classmethod
    async def _execute_vector_search(
        cls,
        database_session: AsyncSession,
        query_vector: List[float],
        filter_document_id: Optional[int],
        filter_user_id: Optional[int],
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        cosine_distance_column = DocumentChunkRecord.embedding_vector.cosine_distance(
            query_vector
        ).label("cosine_distance")

        search_query = (
            select(
                DocumentChunkRecord.id,
                DocumentChunkRecord.document_id,
                DocumentChunkRecord.chunk_index_number,
                DocumentChunkRecord.source_page_number,
                DocumentChunkRecord.chunk_text_content,
                DocumentRecord.filename,
                cosine_distance_column
            )
            .join(DocumentRecord, DocumentChunkRecord.document_id == DocumentRecord.id)
        )

        if filter_document_id is not None:
            search_query = search_query.where(DocumentChunkRecord.document_id == filter_document_id)

        if filter_user_id is not None:
            search_query = search_query.where(DocumentRecord.user_id == filter_user_id)

        search_query = search_query.order_by(cosine_distance_column).limit(limit)
        query_result = await database_session.execute(search_query)
        matching_rows = query_result.all()

        vector_results = []
        for rank_idx, row in enumerate(matching_rows, start=1):
            raw_distance = float(row.cosine_distance) if row.cosine_distance is not None else 1.0
            similarity_ratio = max(0.0, min(1.0, 1.0 - raw_distance))
            vector_results.append({
                "chunk_id": row.id,
                "document_id": row.document_id,
                "chunk_index_number": row.chunk_index_number,
                "document_filename": row.filename,
                "source_page_number": row.source_page_number,
                "chunk_text_content": row.chunk_text_content,
                "similarity_percentage": round(similarity_ratio * 100.0, 2),
                "vector_rank": rank_idx
            })

        return vector_results

    @classmethod
    async def _execute_lexical_search(
        cls,
        database_session: AsyncSession,
        user_query_text: str,
        filter_document_id: Optional[int],
        filter_user_id: Optional[int],
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        cleaned_terms = [
            t.lower() for t in re.findall(r"\w+", user_query_text)
            if len(t) > 2 and t.lower() not in {"what", "when", "where", "which", "about", "this", "that", "with", "from"}
        ]

        if not cleaned_terms:
            return []

        base_query = (
            select(
                DocumentChunkRecord.id,
                DocumentChunkRecord.document_id,
                DocumentChunkRecord.chunk_index_number,
                DocumentChunkRecord.source_page_number,
                DocumentChunkRecord.chunk_text_content,
                DocumentRecord.filename
            )
            .join(DocumentRecord, DocumentChunkRecord.document_id == DocumentRecord.id)
        )

        if filter_document_id is not None:
            base_query = base_query.where(DocumentChunkRecord.document_id == filter_document_id)

        if filter_user_id is not None:
            base_query = base_query.where(DocumentRecord.user_id == filter_user_id)

        term_conditions = [
            DocumentChunkRecord.chunk_text_content.ilike(f"%{term}%")
            for term in cleaned_terms[:6]
        ]
        base_query = base_query.where(or_(*term_conditions)).limit(60)

        query_result = await database_session.execute(base_query)
        rows = query_result.all()

        scored_lexical_items = []
        clean_full_query = user_query_text.lower().strip()

        for row in rows:
            content_lower = row.chunk_text_content.lower()
            term_score = 0.0
            for term in cleaned_terms:
                freq = content_lower.count(term)
                if freq > 0:
                    term_score += 1.0 + math.log(1.0 + freq)

            if clean_full_query in content_lower:
                term_score += 5.0

            scored_lexical_items.append((term_score, {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "chunk_index_number": row.chunk_index_number,
                "document_filename": row.filename,
                "source_page_number": row.source_page_number,
                "chunk_text_content": row.chunk_text_content,
                "lexical_raw_score": term_score
            }))

        scored_lexical_items.sort(key=lambda x: x[0], reverse=True)

        lexical_results = []
        for rank_idx, (_, chunk_data) in enumerate(scored_lexical_items[:limit], start=1):
            chunk_data["bm25_rank"] = rank_idx
            lexical_results.append(chunk_data)

        return lexical_results

    @classmethod
    def _reciprocal_rank_fusion(
        cls,
        vector_candidates: List[Dict[str, Any]],
        lexical_candidates: List[Dict[str, Any]],
        rrf_k: int = 60,
        top_n: int = 15
    ) -> List[Dict[str, Any]]:
        candidate_pool: Dict[int, Dict[str, Any]] = {}
        rrf_scores: Dict[int, float] = {}

        for item in vector_candidates:
            cid = item["chunk_id"]
            candidate_pool[cid] = dict(item)
            rank = item.get("vector_rank", 100)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        for item in lexical_candidates:
            cid = item["chunk_id"]
            if cid not in candidate_pool:
                candidate_pool[cid] = dict(item)
                candidate_pool[cid]["similarity_percentage"] = 55.0
            rank = item.get("bm25_rank", 100)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        fused_results = []
        for cid in sorted_ids[:top_n]:
            chunk_item = candidate_pool[cid]
            chunk_item["rrf_score"] = round(rrf_scores[cid] * 1000.0, 3)
            fused_results.append(chunk_item)

        return fused_results
