import asyncio
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import DocumentChunkRecord, DocumentRecord
from services.embedding_service import VectorEmbeddingGenerator
from services.rerank_service import CandidateRerankerService

class VectorSimilaritySearchEngine:
    @staticmethod
    async def find_most_relevant_chunks(
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

        candidate_fetch_limit = 25 if filter_document_id is not None else max(maximum_results_count * 4, 35)
        search_query = search_query.order_by(cosine_distance_column).limit(candidate_fetch_limit)

        query_result = await database_session.execute(search_query)
        matching_rows = query_result.all()

        initial_candidates = []
        for single_row in matching_rows:
            raw_distance = float(single_row.cosine_distance) if single_row.cosine_distance is not None else 1.0
            similarity_ratio = max(0.0, min(1.0, 1.0 - raw_distance))
            initial_candidates.append({
                "chunk_id": single_row.id,
                "document_id": single_row.document_id,
                "chunk_index_number": single_row.chunk_index_number,
                "document_filename": single_row.filename,
                "source_page_number": single_row.source_page_number,
                "chunk_text_content": single_row.chunk_text_content,
                "similarity_percentage": round(similarity_ratio * 100.0, 2),
                "rerank_score": round(similarity_ratio * 100.0, 2)
            })

        reranked_chunks = CandidateRerankerService.rerank_chunks(
            query_text=user_query_text,
            retrieved_chunks=initial_candidates,
            top_k=maximum_results_count
        )

        return reranked_chunks, query_vector
