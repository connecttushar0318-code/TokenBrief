import uuid
import time
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, delete, func
from typing import Optional, List
from config import settings
from database import get_database_session, database_session_factory
from models import (
    UserAccount,
    DocumentRecord,
    DocumentChunkRecord,
    SemanticQueryCacheRecord,
    ConversationThreadRecord,
    ConversationMessageRecord
)
from schemas import (
    QuestionQueryRequest,
    AnswerWithSourcesResponse,
    SystemHealthStatusResponse,
    SourceReferenceChunk,
    CreateConversationRequest,
    ConversationThreadResponse,
    ConversationMessageRequest,
    ConversationMessageResponse,
    QuickChatRequest,
    QuickChatResponse,
    GenericMessageResponse
)
from security import get_optional_authenticated_user, get_authenticated_user
from services.search_service import VectorSimilaritySearchEngine
from services.rerank_service import CandidateRerankerService
from services.embedding_service import VectorEmbeddingGenerator
from services.qa_service import (
    DocumentQuestionAnsweringService,
    ask_tokenbrief,
    clean_text,
    build_full_file_digest,
    is_pure_greeting,
    LLMClient
)
from services.cache_service import SemanticQueryCacheService
from services.analytics_service import AnalyticsDashboardService
from services.query_router import QueryIntentRouterService, QueryIntent
from services.hierarchical_service import HierarchicalDocumentSummaryService
from services.guardrails_service import HallucinationGuardrailService
from services.comparison_service import DocumentComparisonService

router = APIRouter(prefix="/api/qa", tags=["Q&A"])


SESSION_MEMORY_BUFFER = {}

def _can_use_document_cache(
    message_text: str,
    document_id: Optional[int],
    matched_chunks: List[dict]
) -> bool:
    if document_id is None or not matched_chunks:
        return False
    lower = message_text.lower().strip()
    if any(lower.startswith(g) or lower == g for g in ["hlo", "hello", "hi", "hey", "hola", "thanks"]):
        return False
    return all(chunk.get("document_id") == document_id for chunk in matched_chunks)

async def _bg_record_query_log(
    question_text: str,
    latency_ms: float,
    cache_hit: bool,
    model_used: str,
    estimated_token_count: int,
    user_id: Optional[int],
    document_id: Optional[int],
) -> None:
    try:
        async with database_session_factory() as bg_session:
            await AnalyticsDashboardService.record_query_log(
                database_session=bg_session,
                question_text=question_text,
                latency_ms=latency_ms,
                cache_hit=cache_hit,
                model_used=model_used,
                estimated_token_count=estimated_token_count,
                user_id=user_id,
                document_id=document_id,
            )
    except Exception:
        pass


async def _bg_store_semantic_cache(
    query_text: str,
    query_vector: List[float],
    answer_text: str,
    sources: list,
    document_id: int,
) -> None:
    try:
        async with database_session_factory() as bg_session:
            await SemanticQueryCacheService.store_query_cache(
                database_session=bg_session,
                query_text=query_text,
                query_vector=query_vector,
                answer_text=answer_text,
                sources=sources,
                document_id=document_id,
            )
    except Exception:
        pass


async def _bg_increment_cache_hit(record_id: int) -> None:
    try:
        async with database_session_factory() as bg_session:
            await SemanticQueryCacheService.increment_hit_count(bg_session, record_id)
    except Exception:
        pass


async def _execute_unified_qa(
    message_text: str,
    target_doc_id: Optional[int],
    user_id: Optional[int],
    user_doc_inventory: List[dict],
    database_session: AsyncSession,
    background_tasks: Optional[BackgroundTasks] = None,
) -> tuple:
    active_filename = "Workspace Documents"
    effective_doc_id = target_doc_id
    if target_doc_id:
        match_doc = next((d for d in user_doc_inventory if d["id"] == target_doc_id), None)
        if match_doc:
            active_filename = match_doc["filename"]
    elif user_doc_inventory:
        active_filename = user_doc_inventory[0]["filename"]
        effective_doc_id = user_doc_inventory[0]["id"]

    # 0. Fast-path pure greetings (zero DB chunk scans, zero embeddings, zero LLM wait)
    if is_pure_greeting(message_text):
        result = await ask_tokenbrief(
            user_message=message_text,
            file_name=active_filename,
            all_file_chunks=[],
            top_k_chunks=[],
            llm_client=LLMClient
        )
        return result, [], [], False

    query_vector = VectorEmbeddingGenerator.generate_single_embedding(message_text)

    # 1. Semantic cache lookup when scoped to a concrete document (L1 in-memory first, L2 pgvector fallback)
    if effective_doc_id is not None:
        try:
            cached = await SemanticQueryCacheService.get_cached_answer(
                database_session=database_session,
                query_vector=query_vector,
                filter_document_id=effective_doc_id,
                defer_hit_update=True,
            )
            if cached and cached.get("answer"):
                if background_tasks is not None and cached.get("record_id"):
                    background_tasks.add_task(_bg_increment_cache_hit, int(cached["record_id"]))
                cached_sources = [
                    SourceReferenceChunk(
                        chunk_id=int(s.get("chunk_id", 0)),
                        document_id=int(s.get("document_id", effective_doc_id)),
                        document_filename=str(s.get("document_filename", active_filename)),
                        source_page_number=s.get("source_page_number"),
                        chunk_text_content=str(s.get("chunk_text_content", "")),
                        similarity_percentage=float(s.get("similarity_percentage", 95.0)),
                        rerank_score=s.get("rerank_score")
                    )
                    for s in cached.get("sources", [])
                ]
                return {"answer": cached["answer"], "cited_pages": []}, cached_sources, query_vector, True
        except Exception:
            pass

    # 2. Fetch ONLY lightweight text columns (skip transferring huge 384-float vectors over wire)
    chunks_query = select(
        DocumentChunkRecord.id,
        DocumentChunkRecord.document_id,
        DocumentChunkRecord.source_page_number,
        DocumentChunkRecord.chunk_text_content,
    )
    if target_doc_id:
        chunks_query = chunks_query.where(DocumentChunkRecord.document_id == target_doc_id)
    elif user_doc_inventory:
        chunks_query = chunks_query.where(DocumentChunkRecord.document_id == user_doc_inventory[0]["id"])
    else:
        chunks_query = chunks_query.limit(120)

    chunks_query = chunks_query.order_by(DocumentChunkRecord.source_page_number, DocumentChunkRecord.chunk_index_number).limit(150)
    chunks_result = await database_session.execute(chunks_query)
    all_chunk_records = chunks_result.all()

    all_file_chunks = [
        {
            "chunk_id": c.id,
            "document_id": c.document_id,
            "page": c.source_page_number or 1,
            "text": c.chunk_text_content,
        }
        for c in all_chunk_records
    ]

    # 3. For small single-document queries (<= 5 chunks), rank directly in-memory without redundant DB queries
    if target_doc_id and 0 < len(all_file_chunks) <= 5:
        in_memory_candidates = [
            {
                "chunk_id": c["chunk_id"],
                "document_id": c["document_id"],
                "document_filename": active_filename,
                "source_page_number": c["page"],
                "chunk_text_content": c["text"],
                "similarity_percentage": 85.0,
            }
            for c in all_file_chunks
        ]
        matched_chunks = CandidateRerankerService.rerank_chunks(
            query_text=message_text,
            retrieved_chunks=in_memory_candidates,
            top_k=5,
        )
    else:
        matched_chunks, query_vector = await VectorSimilaritySearchEngine.find_most_relevant_chunks(
            database_session=database_session,
            user_query_text=message_text,
            filter_document_id=target_doc_id,
            filter_user_id=user_id,
            maximum_results_count=5
        )

    top_k_chunks = [
        {
            "chunk_id": c["chunk_id"],
            "document_id": c["document_id"],
            "document_filename": c.get("document_filename", active_filename),
            "page": c.get("source_page_number") or 1,
            "text": c.get("chunk_text_content", ""),
            "similarity_percentage": c.get("similarity_percentage", 0.0),
            "rerank_score": c.get("rerank_score")
        }
        for c in matched_chunks
    ]

    # 4. Call the single unified function: ask_tokenbrief
    result = await ask_tokenbrief(
        user_message=message_text,
        file_name=active_filename,
        all_file_chunks=all_file_chunks,
        top_k_chunks=top_k_chunks,
        llm_client=LLMClient
    )

    # 5. Build sources ONLY from pages the AI actually used
    sources = []
    cited_pages = set(result.get("cited_pages", []))
    if cited_pages:
        for page_num in sorted(list(cited_pages)):
            match = next((c for c in top_k_chunks if c.get("page") == page_num), None)
            if not match:
                match = next((c for c in all_file_chunks if c.get("page") == page_num), None)
            if match:
                sources.append(
                    SourceReferenceChunk(
                        chunk_id=match.get("chunk_id", 0),
                        document_id=match.get("document_id", target_doc_id or 0),
                        document_filename=match.get("document_filename", active_filename),
                        source_page_number=page_num,
                        chunk_text_content=clean_text(match.get("text", "")),
                        similarity_percentage=match.get("similarity_percentage", 95.0),
                        rerank_score=match.get("rerank_score")
                    )
                )

    # 6. Store in semantic cache asynchronously (updates L1 immediately inside helper or background task)
    if effective_doc_id is not None and result.get("answer") and all_file_chunks:
        serializable_sources = [s.model_dump() for s in sources]
        SemanticQueryCacheService._save_to_l1(
            document_id=effective_doc_id,
            query_text=message_text,
            query_vector=query_vector,
            answer_text=result["answer"],
            sources=serializable_sources,
        )
        if background_tasks is not None:
            background_tasks.add_task(
                _bg_store_semantic_cache,
                message_text,
                query_vector,
                result["answer"],
                serializable_sources,
                effective_doc_id,
            )

    return result, sources, query_vector, False

@router.post("/ask", response_model=AnswerWithSourcesResponse)
async def ask_document_question(
    question_payload: QuestionQueryRequest,
    background_tasks: BackgroundTasks,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    start_execution_time = time.perf_counter()
    try:
        user_identifier_id = optional_user_account.id if optional_user_account else None
        target_doc_id = question_payload.filter_document_id
        if target_doc_id == 0:
            target_doc_id = None

        inventory_stmt = select(DocumentRecord.id, DocumentRecord.filename, DocumentRecord.total_page_count)
        if user_identifier_id:
            inventory_stmt = inventory_stmt.where(DocumentRecord.user_id == user_identifier_id)
        inventory_result = await database_session.execute(inventory_stmt)
        user_doc_inventory = [
            {"id": row.id, "filename": row.filename, "pages": row.total_page_count or 1}
            for row in inventory_result.all()
        ]

        result, sources, query_vector, is_cache_hit = await _execute_unified_qa(
            message_text=question_payload.question_text,
            target_doc_id=target_doc_id,
            user_id=user_identifier_id,
            user_doc_inventory=user_doc_inventory,
            database_session=database_session,
            background_tasks=background_tasks,
        )

        latency_ms = (time.perf_counter() - start_execution_time) * 1000.0
        active_model = settings.gemini_model_name if (settings.gemini_api_key and settings.gemini_api_key not in LLMClient._invalid_keys) else "TokenBrief Unified Engine"
        background_tasks.add_task(
            _bg_record_query_log,
            question_payload.question_text,
            latency_ms,
            is_cache_hit,
            active_model,
            max(15, (len(question_payload.question_text) + len(result["answer"])) // 4),
            user_identifier_id,
            target_doc_id,
        )

        return AnswerWithSourcesResponse(
            question_text=question_payload.question_text,
            generated_answer=result["answer"],
            source_chunks=sources,
            cache_hit=is_cache_hit
        )

    except ValueError as validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(validation_error)
        )
    except Exception as runtime_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(runtime_error)}"
        )

@router.post("/quick-chat", response_model=QuickChatResponse)
async def convenient_quick_chat(
    payload: QuickChatRequest,
    background_tasks: BackgroundTasks,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    start_execution_time = time.perf_counter()
    session_id = payload.session_id or uuid.uuid4().hex
    user_id = optional_user_account.id if optional_user_account else None
    target_doc_id = payload.document_id or None

    inventory_stmt = select(DocumentRecord.id, DocumentRecord.filename, DocumentRecord.total_page_count)
    if user_id:
        inventory_stmt = inventory_stmt.where(DocumentRecord.user_id == user_id)
    inventory_result = await database_session.execute(inventory_stmt)
    user_doc_inventory = [
        {"id": row.id, "filename": row.filename, "pages": row.total_page_count or 1}
        for row in inventory_result.all()
    ]

    result, sources, query_vector, is_cache_hit = await _execute_unified_qa(
        message_text=payload.message_text,
        target_doc_id=target_doc_id,
        user_id=user_id,
        user_doc_inventory=user_doc_inventory,
        database_session=database_session,
        background_tasks=background_tasks,
    )

    answer_text = result["answer"]

    history_records = SESSION_MEMORY_BUFFER.get(session_id, [])
    history_records.append({"role": "user", "content": payload.message_text})
    history_records.append({"role": "assistant", "content": answer_text})
    if len(history_records) > 8:
        history_records = history_records[-8:]
    SESSION_MEMORY_BUFFER[session_id] = history_records

    latency_ms = (time.perf_counter() - start_execution_time) * 1000.0
    active_model = settings.gemini_model_name if (settings.gemini_api_key and settings.gemini_api_key not in LLMClient._invalid_keys) else "TokenBrief Unified Engine"
    background_tasks.add_task(
        _bg_record_query_log,
        payload.message_text,
        latency_ms,
        is_cache_hit,
        active_model,
        max(15, (len(payload.message_text) + len(answer_text)) // 4),
        user_id,
        target_doc_id,
    )

    return QuickChatResponse(
        session_id=session_id,
        answer=answer_text,
        sources=sources,
        cache_hit=is_cache_hit
    )

@router.get("/cache/stats")
async def get_semantic_cache_statistics(
    database_session: AsyncSession = Depends(get_database_session)
):
    count_query = select(func.count(SemanticQueryCacheRecord.id), func.sum(SemanticQueryCacheRecord.hit_count))
    result = await database_session.execute(count_query)
    total_entries, total_hits = result.first()
    return {
        "total_cached_queries": total_entries or 0,
        "total_cache_hits": total_hits or 0,
        "status": "active"
    }

@router.delete("/cache", response_model=GenericMessageResponse)
async def clear_semantic_cache(
    database_session: AsyncSession = Depends(get_database_session)
):
    SemanticQueryCacheService.clear_memory_cache()
    await database_session.execute(delete(SemanticQueryCacheRecord))
    await database_session.commit()
    return GenericMessageResponse(message="Semantic cache cleared successfully")

@router.post("/conversations", response_model=ConversationThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation_thread(
    payload: CreateConversationRequest,
    database_session: AsyncSession = Depends(get_database_session),
    current_user: UserAccount = Depends(get_authenticated_user)
):
    thread = ConversationThreadRecord(
        user_id=current_user.id,
        document_id=payload.document_id,
        title=payload.title
    )
    database_session.add(thread)
    await database_session.commit()
    await database_session.refresh(thread)
    return thread

@router.get("/conversations", response_model=List[ConversationThreadResponse])
async def list_user_conversations(
    database_session: AsyncSession = Depends(get_database_session),
    current_user: UserAccount = Depends(get_authenticated_user)
):
    stmt = (
        select(ConversationThreadRecord)
        .where(ConversationThreadRecord.user_id == current_user.id)
        .order_by(ConversationThreadRecord.created_at.desc())
    )
    result = await database_session.execute(stmt)
    return result.scalars().all()

@router.get("/conversations/{thread_id}", response_model=ConversationThreadResponse)
async def get_conversation_history(
    thread_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    current_user: UserAccount = Depends(get_authenticated_user)
):
    stmt = select(ConversationThreadRecord).where(
        ConversationThreadRecord.id == thread_id,
        ConversationThreadRecord.user_id == current_user.id
    )
    result = await database_session.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Conversation thread not found")

    msg_stmt = (
        select(ConversationMessageRecord)
        .where(ConversationMessageRecord.thread_id == thread_id)
        .order_by(ConversationMessageRecord.created_at.asc())
    )
    msg_result = await database_session.execute(msg_stmt)
    thread.messages = msg_result.scalars().all()
    return thread

@router.post("/conversations/{thread_id}/messages", response_model=AnswerWithSourcesResponse)
async def send_message_in_thread(
    thread_id: int,
    payload: ConversationMessageRequest,
    database_session: AsyncSession = Depends(get_database_session),
    current_user: UserAccount = Depends(get_authenticated_user)
):
    stmt = select(ConversationThreadRecord).where(
        ConversationThreadRecord.id == thread_id,
        ConversationThreadRecord.user_id == current_user.id
    )
    result = await database_session.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Conversation thread not found")

    user_msg = ConversationMessageRecord(
        thread_id=thread_id,
        sender_role="user",
        message_text=payload.message_text
    )
    database_session.add(user_msg)

    thread_doc_id = thread.document_id

    inventory_stmt = select(DocumentRecord.id, DocumentRecord.filename, DocumentRecord.total_page_count).where(DocumentRecord.user_id == current_user.id)
    inventory_result = await database_session.execute(inventory_stmt)
    user_doc_inventory = [
        {"id": row.id, "filename": row.filename, "pages": row.total_page_count or 1}
        for row in inventory_result.all()
    ]

    result, source_references, _ = await _execute_unified_qa(
        message_text=payload.message_text,
        target_doc_id=thread_doc_id,
        user_id=current_user.id,
        user_doc_inventory=user_doc_inventory,
        database_session=database_session
    )

    model_answer = result["answer"]

    bot_msg = ConversationMessageRecord(
        thread_id=thread_id,
        sender_role="assistant",
        message_text=model_answer
    )
    database_session.add(bot_msg)
    await database_session.commit()

    return AnswerWithSourcesResponse(
        question_text=payload.message_text,
        generated_answer=model_answer,
        source_chunks=source_references
    )

@router.get("/health", response_model=SystemHealthStatusResponse)
async def check_system_health(
    database_session: AsyncSession = Depends(get_database_session)
):
    database_connectivity_status = "connected"
    try:
        await database_session.execute(text("SELECT 1"))
    except Exception:
        database_connectivity_status = "disconnected"

    return SystemHealthStatusResponse(
        service_status="operational",
        database_status=database_connectivity_status
    )
