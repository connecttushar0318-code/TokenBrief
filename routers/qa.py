import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, delete, func
from typing import Optional, List
from database import get_database_session
from models import (
    UserAccount,
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
from services.qa_service import DocumentQuestionAnsweringService
from services.cache_service import SemanticQueryCacheService

router = APIRouter(prefix="/api/qa", tags=["Q&A"])


SESSION_MEMORY_BUFFER = {}

def _can_use_document_cache(
    message_text: str,
    document_id: Optional[int],
    matched_chunks: List[dict]
) -> bool:
    if document_id is None or not matched_chunks:
        return False
    if DocumentQuestionAnsweringService.is_greeting(message_text):
        return False
    return all(chunk.get("document_id") == document_id for chunk in matched_chunks)

@router.post("/ask", response_model=AnswerWithSourcesResponse)
async def ask_document_question(
    question_payload: QuestionQueryRequest,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        user_identifier_id = optional_user_account.id if optional_user_account else None
        target_doc_id = question_payload.filter_document_id
        if target_doc_id == 0:
            target_doc_id = None

        matched_chunks, query_vector = await VectorSimilaritySearchEngine.find_most_relevant_chunks(
            database_session=database_session,
            user_query_text=question_payload.question_text,
            filter_document_id=target_doc_id,
            filter_user_id=user_identifier_id,
            maximum_results_count=question_payload.maximum_results
        )

        can_use_cache = _can_use_document_cache(
            question_payload.question_text,
            target_doc_id,
            matched_chunks
        )
        cached_hit = None
        if can_use_cache:
            cached_hit = await SemanticQueryCacheService.get_cached_answer(
                database_session=database_session,
                query_vector=query_vector,
                filter_document_id=target_doc_id
            )

        if cached_hit:
            return AnswerWithSourcesResponse(
                question_text=question_payload.question_text,
                generated_answer=cached_hit["answer"],
                source_chunks=[SourceReferenceChunk(**s) for s in cached_hit["sources"]],
                cache_hit=True,
                cached_query=cached_hit["cached_query"]
            )

        user_name_identifier = optional_user_account.username if optional_user_account else None
        model_answer = DocumentQuestionAnsweringService.generate_grounded_answer(
            user_question_text=question_payload.question_text,
            retrieved_context_chunks=matched_chunks,
            user_name=user_name_identifier
        )

        source_references = [
            SourceReferenceChunk(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
                document_filename=chunk["document_filename"],
                source_page_number=chunk["source_page_number"],
                chunk_text_content=chunk["chunk_text_content"],
                similarity_percentage=chunk["similarity_percentage"],
                rerank_score=chunk.get("rerank_score")
            )
            for chunk in matched_chunks
        ]

        if can_use_cache:
            await SemanticQueryCacheService.store_query_cache(
                database_session=database_session,
                query_text=question_payload.question_text,
                query_vector=query_vector,
                answer_text=model_answer,
                sources=[s.model_dump() for s in source_references],
                document_id=target_doc_id
            )

        return AnswerWithSourcesResponse(
            question_text=question_payload.question_text,
            generated_answer=model_answer,
            source_chunks=source_references,
            cache_hit=False
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
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    session_id = payload.session_id or uuid.uuid4().hex
    user_id = optional_user_account.id if optional_user_account else None

    target_doc_id = payload.document_id or None

    matched_chunks, query_vector = await VectorSimilaritySearchEngine.find_most_relevant_chunks(
        database_session=database_session,
        user_query_text=payload.message_text,
        filter_document_id=target_doc_id,
        filter_user_id=user_id,
        maximum_results_count=10 if target_doc_id is not None else 8
    )

    can_use_cache = _can_use_document_cache(
        payload.message_text,
        target_doc_id,
        matched_chunks
    )
    cached_hit = None
    if can_use_cache:
        cached_hit = await SemanticQueryCacheService.get_cached_answer(
            database_session=database_session,
            query_vector=query_vector,
            filter_document_id=target_doc_id
        )

    if cached_hit:
        return QuickChatResponse(
            session_id=session_id,
            answer=cached_hit["answer"],
            sources=[SourceReferenceChunk(**s) for s in cached_hit["sources"]],
            cache_hit=True
        )

    user_name_identifier = optional_user_account.username if optional_user_account else None
    history_records = SESSION_MEMORY_BUFFER.get(session_id, [])
    model_answer = DocumentQuestionAnsweringService.generate_grounded_answer(
        user_question_text=payload.message_text,
        retrieved_context_chunks=matched_chunks,
        user_name=user_name_identifier,
        conversation_history=history_records
    )
    history_records.append({"role": "user", "content": payload.message_text})
    history_records.append({"role": "assistant", "content": model_answer})
    if len(history_records) > 8:
        history_records = history_records[-8:]
    SESSION_MEMORY_BUFFER[session_id] = history_records

    sources = [
        SourceReferenceChunk(
            chunk_id=c["chunk_id"],
            document_id=c["document_id"],
            document_filename=c["document_filename"],
            source_page_number=c["source_page_number"],
            chunk_text_content=c["chunk_text_content"],
            similarity_percentage=c["similarity_percentage"],
            rerank_score=c.get("rerank_score")
        )
        for c in matched_chunks
    ]

    if can_use_cache:
        await SemanticQueryCacheService.store_query_cache(
            database_session=database_session,
            query_text=payload.message_text,
            query_vector=query_vector,
            answer_text=model_answer,
            sources=[s.model_dump() for s in sources],
            document_id=target_doc_id
        )

    return QuickChatResponse(
        session_id=session_id,
        answer=model_answer,
        sources=sources,
        cache_hit=False
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

    matched_chunks, query_vector = await VectorSimilaritySearchEngine.find_most_relevant_chunks(
        database_session=database_session,
        user_query_text=payload.message_text,
        filter_document_id=thread.document_id,
        filter_user_id=current_user.id,
        maximum_results_count=10 if target_doc_id is not None else 8
    )

    model_answer = DocumentQuestionAnsweringService.generate_grounded_answer(
        user_question_text=payload.message_text,
        retrieved_context_chunks=matched_chunks,
        user_name=current_user.username
    )

    bot_msg = ConversationMessageRecord(
        thread_id=thread_id,
        sender_role="assistant",
        message_text=model_answer
    )
    database_session.add(bot_msg)
    await database_session.commit()

    source_references = [
        SourceReferenceChunk(
            chunk_id=chunk["chunk_id"],
            document_id=chunk["document_id"],
            document_filename=chunk["document_filename"],
            source_page_number=chunk["source_page_number"],
            chunk_text_content=chunk["chunk_text_content"],
            similarity_percentage=chunk["similarity_percentage"],
            rerank_score=chunk.get("rerank_score")
        )
        for chunk in matched_chunks
    ]

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
