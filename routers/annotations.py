from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from database import get_database_session
from models import UserAccount, UserAnnotationRecord, DocumentRecord, DocumentChunkRecord
from security import get_authenticated_user, get_optional_authenticated_user
from schemas import (
    CreateAnnotationRequest,
    UpdateAnnotationRequest,
    UserAnnotationResponse,
    DocumentAnnotationsResponse,
    GenericMessageResponse
)

router = APIRouter(prefix="/api/annotations", tags=["Annotations & Highlights"])

@router.post("", response_model=UserAnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_user_annotation(
    annotation_payload: CreateAnnotationRequest,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: UserAccount = Depends(get_authenticated_user)
):
    doc_query = select(DocumentRecord).where(DocumentRecord.id == annotation_payload.document_id)
    doc_result = await database_session.execute(doc_query)
    document_record = doc_result.scalar_one_or_none()

    if not document_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {annotation_payload.document_id} was not found."
        )

    resolved_page_number = annotation_payload.source_page_number
    if annotation_payload.chunk_id and resolved_page_number is None:
        chunk_query = select(DocumentChunkRecord).where(DocumentChunkRecord.id == annotation_payload.chunk_id)
        chunk_result = await database_session.execute(chunk_query)
        chunk_record = chunk_result.scalar_one_or_none()
        if chunk_record:
            resolved_page_number = chunk_record.source_page_number

    new_annotation = UserAnnotationRecord(
        user_id=authenticated_user.id,
        document_id=annotation_payload.document_id,
        chunk_id=annotation_payload.chunk_id,
        highlighted_text=annotation_payload.highlighted_text,
        annotation_note=annotation_payload.annotation_note,
        color_code=annotation_payload.color_code or "yellow",
        source_page_number=resolved_page_number or 1
    )

    database_session.add(new_annotation)
    await database_session.commit()
    await database_session.refresh(new_annotation)

    return new_annotation

@router.get("/document/{document_id}", response_model=DocumentAnnotationsResponse)
async def get_document_annotations(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    query = (
        select(UserAnnotationRecord)
        .where(UserAnnotationRecord.document_id == document_id)
    )
    if authenticated_user:
        query = query.where(UserAnnotationRecord.user_id == authenticated_user.id)

    query = query.order_by(UserAnnotationRecord.created_at.desc())
    query_result = await database_session.execute(query)
    annotations = list(query_result.scalars().all())

    return DocumentAnnotationsResponse(
        document_id=document_id,
        total_annotations=len(annotations),
        annotations=annotations
    )

@router.get("/chunk/{chunk_id}", response_model=List[UserAnnotationResponse])
async def get_chunk_annotations(
    chunk_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    query = (
        select(UserAnnotationRecord)
        .where(UserAnnotationRecord.chunk_id == chunk_id)
    )
    if authenticated_user:
        query = query.where(UserAnnotationRecord.user_id == authenticated_user.id)

    query = query.order_by(UserAnnotationRecord.created_at.desc())
    query_result = await database_session.execute(query)
    annotations = list(query_result.scalars().all())
    return annotations

@router.put("/{annotation_id}", response_model=UserAnnotationResponse)
async def update_user_annotation(
    annotation_id: int,
    update_payload: UpdateAnnotationRequest,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: UserAccount = Depends(get_authenticated_user)
):
    query = select(UserAnnotationRecord).where(
        UserAnnotationRecord.id == annotation_id,
        UserAnnotationRecord.user_id == authenticated_user.id
    )
    query_result = await database_session.execute(query)
    annotation = query_result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found or unauthorized to edit."
        )

    if update_payload.annotation_note is not None:
        annotation.annotation_note = update_payload.annotation_note
    if update_payload.color_code is not None:
        annotation.color_code = update_payload.color_code

    await database_session.commit()
    await database_session.refresh(annotation)
    return annotation

@router.delete("/{annotation_id}", response_model=GenericMessageResponse)
async def delete_user_annotation(
    annotation_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    authenticated_user: UserAccount = Depends(get_authenticated_user)
):
    query = select(UserAnnotationRecord).where(
        UserAnnotationRecord.id == annotation_id,
        UserAnnotationRecord.user_id == authenticated_user.id
    )
    query_result = await database_session.execute(query)
    annotation = query_result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found or unauthorized to delete."
        )

    await database_session.delete(annotation)
    await database_session.commit()
    return GenericMessageResponse(message="Annotation deleted successfully")
