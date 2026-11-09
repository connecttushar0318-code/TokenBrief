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

    chunk_query = (
        select(DocumentChunkRecord.chunk_text_content)
        .where(DocumentChunkRecord.document_id == document_id)
        .order_by(DocumentChunkRecord.chunk_index_number.asc())
    )
    chunk_res = await database_session.execute(chunk_query)
    chunks = chunk_res.scalars().all()

    stitched_full_text = DocumentQuestionAnsweringService.stitch_overlapping_chunks(chunks)
    cleaned_document_text = DocumentQuestionAnsweringService.clean_extracted_text(stitched_full_text)
    detected_sections = DocumentQuestionAnsweringService.parse_document_sections(cleaned_document_text)

    prompt = (
        "Generate a structured summary for the following document text:\n\n"
        f"{cleaned_document_text[:6000]}\n\n"
        "Format your answer with exactly 3 sections:\n"
        "1. Executive Summary: (2-3 concise sentences explaining the document core contents)\n"
        "2. Key Takeaways: (3-5 bullet points starting with -)\n"
        "3. Topics: (comma-separated list of 3-6 topics)"
    )

    summary_text = ""
    takeaways = []
    topics = []

    if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
        candidate_models = [settings.gemini_model_name, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        for model_name in candidate_models:
            try:
                client = genai.Client(api_key=settings.gemini_api_key)
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                raw = resp.text.strip()
                lines = [line.strip() for line in raw.split("\n") if line.strip()]

                current_section = None
                summary_lines = []
                for line in lines:
                    if "executive summary" in line.lower():
                        current_section = "summary"
                        continue
                    elif "key takeaway" in line.lower():
                        current_section = "takeaways"
                        continue
                    elif "topic" in line.lower():
                        current_section = "topics"
                        continue

                    if current_section == "summary":
                        summary_lines.append(line)
                    elif current_section == "takeaways" and line.startswith("-"):
                        takeaways.append(line.lstrip("- ").strip())
                    elif current_section == "topics":
                        topics.extend([t.strip() for t in line.split(",") if t.strip()])

                summary_text = " ".join(summary_lines)
                if summary_text:
                    break
            except Exception:
                continue

    if not summary_text:
        summary_section_candidate = detected_sections.get("SUMMARY", "") or detected_sections.get("Overview", "") or detected_sections.get("ABSTRACT", "")
        if summary_section_candidate:
            summary_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", summary_section_candidate) if len(s.strip()) > 20]
            summary_text = " ".join(summary_sentences[:3])
            if not summary_text.endswith("."):
                summary_text += "."

        if not summary_text:
            raw_sentences = [s.strip() for s in re.split(r"(?:•|\n|(?<=[.!?])\s+(?=[A-Z]))", cleaned_document_text) if len(s.strip()) > 25]
            if raw_sentences:
                sentence_vectors = await asyncio.to_thread(
                    VectorEmbeddingGenerator.generate_batch_embeddings,
                    raw_sentences[:40]
                )
                dimension = len(sentence_vectors[0]) if sentence_vectors else 0
                if dimension > 0 and len(sentence_vectors) > 1:
                    centroid = [sum(vec[i] for vec in sentence_vectors) / len(sentence_vectors) for i in range(dimension)]
                    scored_sentences = []
                    for s_idx in range(len(sentence_vectors)):
                        vec = sentence_vectors[s_idx]
                        dot = sum(a * b for a, b in zip(vec, centroid))
                        mag_a = (sum(a * a for a in vec)) ** 0.5
                        mag_b = (sum(b * b for b in centroid)) ** 0.5
                        sim = dot / (mag_a * mag_b) if mag_a * mag_b > 0 else 0
                        scored_sentences.append((sim, raw_sentences[s_idx]))
                    scored_sentences.sort(key=lambda x: x[0], reverse=True)
                    top_sentences = [item[1] for item in scored_sentences[:3]]
                    summary_text = " ".join(top_sentences)
                else:
                    summary_text = " ".join(raw_sentences[:2])
            else:
                summary_text = f"Document '{document.filename}' consists of {document.total_page_count} pages and {document.total_chunk_count} indexed sections."

        structured_takeaways = []
        if "EDUCATION" in detected_sections:
            edu_bullets = DocumentQuestionAnsweringService.extract_clean_bullets(detected_sections["EDUCATION"])
            for b in edu_bullets:
                if any(k in b.lower() for k in ["cgpa", "b.tech", "degree", "university", "college", "studies"]):
                    structured_takeaways.append(b)
                    break

        if "ACHIEVEMENTS & ACTIVITIES" in detected_sections or "ACHIEVEMENTS" in detected_sections:
            ach_text = detected_sections.get("ACHIEVEMENTS & ACTIVITIES", "") or detected_sections.get("ACHIEVEMENTS", "")
            ach_bullets = DocumentQuestionAnsweringService.extract_clean_bullets(ach_text)
            for b in ach_bullets:
                if any(k in b.lower() for k in ["cgpa", "sgpa", "perfect", "award", "rank"]):
                    structured_takeaways.append(b)
                    break

        if "SKILLS" in detected_sections or "TECHNICAL SKILLS" in detected_sections:
            sk_text = detected_sections.get("SKILLS", "") or detected_sections.get("TECHNICAL SKILLS", "")
            lines = [l.strip() for l in sk_text.split("\n") if l.strip()]
            if lines:
                structured_takeaways.append(lines[0])

        if "INTERNSHIP EXPERIENCE" in detected_sections or "EXPERIENCE" in detected_sections:
            exp_text = detected_sections.get("INTERNSHIP EXPERIENCE", "") or detected_sections.get("EXPERIENCE", "")
            exp_bullets = DocumentQuestionAnsweringService.extract_clean_bullets(exp_text)
            if exp_bullets:
                joined_bullet = exp_bullets[0] + (" - " + exp_bullets[1] if len(exp_bullets) > 1 else "")
                structured_takeaways.append(joined_bullet)

        if "PROJECTS" in detected_sections:
            proj_text = detected_sections["PROJECTS"]
            proj_bullets = DocumentQuestionAnsweringService.extract_clean_bullets(proj_text)
            proj_titles = [b.split("|")[0].replace("GitHub", "").replace("Live Demo", "").strip() for b in proj_bullets if "|" in b]
            if proj_titles:
                structured_takeaways.append("Featured Projects: " + ", ".join(proj_titles[:3]))

        if "CERTIFICATIONS" in detected_sections:
            cert_bullets = DocumentQuestionAnsweringService.extract_clean_bullets(detected_sections["CERTIFICATIONS"])
            if cert_bullets:
                structured_takeaways.append("Certifications: " + cert_bullets[0])

        if not structured_takeaways:
            all_clean_bullets = DocumentQuestionAnsweringService.extract_clean_bullets(cleaned_document_text)
            structured_takeaways = all_clean_bullets[:5]

        takeaways = structured_takeaways

        topic_candidates = []
        domain_patterns = [
            r"\bArtificial Intelligence\b", r"\bMachine Learning\b", r"\bData Science\b",
            r"\bPython\b", r"\bSQL\b", r"\bStreamlit\b", r"\bXGBoost\b", r"\bScikit-learn\b",
            r"\bNLP\b", r"\bDeep Learning\b", r"\bNeural Networks\b", r"\bFraud Detection\b",
            r"\bRecommendation System\b", r"\bData Analytics\b", r"\bMySQL\b", r"\bPower BI\b"
        ]
        for pat in domain_patterns:
            matched_object = re.search(pat, cleaned_document_text, re.IGNORECASE)
            if matched_object:
                matched_label = matched_object.group(0)
                if matched_label not in topic_candidates:
                    topic_candidates.append(matched_label)

        if len(topic_candidates) < 4:
            word_tokens = [w.strip() for w in re.findall(r"\b[A-Za-z]{4,}\b", cleaned_document_text)]
            word_frequencies = {}
            stop_words = {"this", "that", "with", "from", "have", "were", "been", "their", "about", "which", "will", "would", "could", "should"}
            for word in word_tokens:
                lowered = word.lower()
                if lowered not in stop_words:
                    word_frequencies[word.capitalize()] = word_frequencies.get(word.capitalize(), 0) + 1
            sorted_topics = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
            for topic_name, _ in sorted_topics:
                if topic_name not in topic_candidates:
                    topic_candidates.append(topic_name)
                if len(topic_candidates) >= 6:
                    break

        topics = topic_candidates[:6] or ["Intelligence", "Analytics", "Engineering", "Technology"]

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
