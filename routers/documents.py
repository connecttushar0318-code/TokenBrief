import asyncio
import re
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings
from database import get_database_session
from models import DocumentRecord, DocumentChunkRecord, UserAccount
from schemas import (
    DocumentMetadataResponse,
    DocumentSummaryResponse,
    DocumentComparisonRequest,
    DocumentComparisonResponse
)
from security import get_optional_authenticated_user
from services.pdf_service import PDFTextExtractor
from services.chunking_service import DocumentTextChunker
from services.embedding_service import VectorEmbeddingGenerator
from services.qa_service import DocumentQuestionAnsweringService
from services.comparison_service import DocumentComparisonService
from services.hierarchical_service import HierarchicalDocumentSummaryService
from google import genai

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    uploaded_file: UploadFile = File(...),
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    original_filename = uploaded_file.filename or "uploaded_file"
    file_suffix = Path(original_filename).suffix.lower()

    if file_suffix not in settings.allowed_extensions:
        allowed_list = ", ".join(settings.allowed_extensions)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_suffix}'. Allowed formats: {allowed_list}"
        )

    storage_directory = Path(settings.document_upload_directory)
    storage_directory.mkdir(parents=True, exist_ok=True)

    unique_stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
    destination_file_path = storage_directory / unique_stored_filename

    total_bytes_read = 0
    max_bytes = settings.get_max_upload_bytes()

    try:
        with destination_file_path.open("wb") as file_stream:
            while True:
                chunk_bytes = await uploaded_file.read(1024 * 64)
                if not chunk_bytes:
                    break
                total_bytes_read += len(chunk_bytes)
                if total_bytes_read > max_bytes:
                    destination_file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed upload size of {settings.max_upload_size_mb} MB"
                    )
                file_stream.write(chunk_bytes)
    except HTTPException:
        raise
    except Exception as error_message:
        destination_file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to disk: {str(error_message)}"
        )
    finally:
        await uploaded_file.close()

    if total_bytes_read < settings.min_upload_size_bytes:
        destination_file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too small or empty. Minimum required file size is {settings.min_upload_size_bytes} bytes"
        )

    try:
        extracted_pages = await asyncio.to_thread(
            PDFTextExtractor.extract_text_from_file,
            str(destination_file_path)
        )
        if not extracted_pages:
            destination_file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable text could be extracted from the uploaded document"
            )

        generated_chunks = DocumentTextChunker.split_pages_into_chunks(
            extracted_pages,
            document_filename=original_filename
        )
        if not generated_chunks:
            destination_file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create text chunks from the document"
            )

        text_list_to_embed = [single_chunk["chunk_text"] for single_chunk in generated_chunks]
        computed_embeddings = await asyncio.to_thread(
            VectorEmbeddingGenerator.generate_batch_embeddings,
            text_list_to_embed
        )

        document_record = DocumentRecord(
            user_id=optional_user_account.id if optional_user_account else None,
            filename=original_filename,
            file_path=str(destination_file_path),
            file_size_bytes=total_bytes_read,
            total_page_count=len(extracted_pages),
            total_chunk_count=len(generated_chunks)
        )
        database_session.add(document_record)
        await database_session.flush()

        chunk_records = []
        for chunk_index in range(len(generated_chunks)):
            chunk_data = generated_chunks[chunk_index]
            embedding_vector = computed_embeddings[chunk_index]
            chunk_records.append(
                DocumentChunkRecord(
                    document_id=document_record.id,
                    chunk_index_number=chunk_data["chunk_index"],
                    source_page_number=chunk_data["page_number"],
                    chunk_text_content=chunk_data["chunk_text"],
                    embedding_vector=embedding_vector
                )
            )

        database_session.add_all(chunk_records)
        await database_session.commit()
        await database_session.refresh(document_record)

        try:
            await HierarchicalDocumentSummaryService.index_document_sections(
                document_id=document_record.id,
                database_session=database_session,
                batch_size=5
            )
        except Exception:
            pass

        return document_record

    except HTTPException:
        raise
    except Exception as unexpected_error:
        destination_file_path.unlink(missing_ok=True)
        await database_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the document: {str(unexpected_error)}"
        )

@router.get("", response_model=List[DocumentMetadataResponse])
async def list_uploaded_documents(
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    query = select(DocumentRecord)
    if optional_user_account:
        query = query.where(DocumentRecord.user_id == optional_user_account.id)
    query = query.order_by(DocumentRecord.created_at.desc())
    query_result = await database_session.execute(query)
    return query_result.scalars().all()

@router.get("/search", response_model=List[DocumentMetadataResponse])
async def search_documents_by_filename(
    query_text: str = Query(..., min_length=1),
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    stmt = select(DocumentRecord).where(DocumentRecord.filename.ilike(f"%{query_text}%"))
    if optional_user_account:
        stmt = stmt.where(DocumentRecord.user_id == optional_user_account.id)
    stmt = stmt.order_by(DocumentRecord.created_at.desc())
    result = await database_session.execute(stmt)
    return result.scalars().all()

@router.get("/{document_id}", response_model=DocumentMetadataResponse)
async def get_document_details(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    query = select(DocumentRecord).where(DocumentRecord.id == document_id)
    if optional_user_account:
        query = query.where(DocumentRecord.user_id == optional_user_account.id)
    query_result = await database_session.execute(query)
    found_document = query_result.scalar_one_or_none()
    if not found_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested document was not found"
        )
    return found_document

@router.post("/{document_id}/summary", response_model=DocumentSummaryResponse)
async def generate_document_summary(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    doc_query = select(DocumentRecord).where(DocumentRecord.id == document_id)
    if optional_user_account:
        doc_query = doc_query.where(DocumentRecord.user_id == optional_user_account.id)
    result = await database_session.execute(doc_query)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    hierarchical_data = await HierarchicalDocumentSummaryService.get_or_build_hierarchical_summary(
        document_id=document.id,
        database_session=database_session
    )

    return DocumentSummaryResponse(
        document_id=document.id,
        filename=document.filename,
        executive_summary=hierarchical_data["executive_summary"],
        key_takeaways=hierarchical_data["key_takeaways"],
        topics=hierarchical_data["topics"]
    )

    return DocumentSummaryResponse(
        document_id=document.id,
        filename=document.filename,
        executive_summary=summary_text,
        key_takeaways=takeaways or ["Comprehensive domain overview indexed in knowledge base"],
        topics=topics or ["General", "Analysis", "Data", "Knowledge"]
    )

@router.post("/compare", response_model=DocumentComparisonResponse)
async def compare_multiple_documents(
    comparison_request: DocumentComparisonRequest,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    try:
        comparison_result = await DocumentComparisonService.compare_documents(
            document_ids=comparison_request.document_ids,
            database_session=database_session
        )
        return comparison_result
    except ValueError as val_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_error)
        )
    except Exception as general_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document comparison failed: {str(general_error)}"
        )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_by_id(
    document_id: int,
    database_session: AsyncSession = Depends(get_database_session),
    optional_user_account: Optional[UserAccount] = Depends(get_optional_authenticated_user)
):
    query = select(DocumentRecord).where(DocumentRecord.id == document_id)
    if optional_user_account:
        query = query.where(DocumentRecord.user_id == optional_user_account.id)
    query_result = await database_session.execute(query)
    target_document = query_result.scalar_one_or_none()
    if not target_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    file_on_disk = Path(target_document.file_path)
    file_on_disk.unlink(missing_ok=True)

    await database_session.delete(target_document)
    await database_session.commit()
    return None
