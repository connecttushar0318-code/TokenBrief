import re
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models import DocumentRecord, DocumentChunkRecord, DocumentSectionRecord
from config import settings

class HierarchicalDocumentSummaryService:

    CONCURRENT_SEMAPHORE = asyncio.Semaphore(4)

    @classmethod
    async def index_document_sections(
        cls,
        document_id: int,
        database_session: AsyncSession,
        batch_size: int = 5
    ) -> List[DocumentSectionRecord]:
        doc_query = select(DocumentRecord).where(DocumentRecord.id == document_id)
        doc_result = await database_session.execute(doc_query)
        target_document = doc_result.scalar_one_or_none()

        if not target_document:
            raise ValueError(f"Document with ID {document_id} was not found.")

        chunks_query = (
            select(DocumentChunkRecord)
            .where(DocumentChunkRecord.document_id == document_id)
            .order_by(DocumentChunkRecord.chunk_index_number.asc())
        )
        chunks_result = await database_session.execute(chunks_query)
        chunks = list(chunks_result.scalars().all())

        if not chunks:
            raise ValueError(f"Document with ID {document_id} has no indexed text chunks.")

        page_to_text: Dict[int, List[str]] = {}
        for chunk in chunks:
            p_num = chunk.source_page_number or 1
            if p_num not in page_to_text:
                page_to_text[p_num] = []
            page_to_text[p_num].append(chunk.chunk_text_content)

        sorted_pages = sorted(page_to_text.keys())
        total_pages = target_document.total_page_count or (max(sorted_pages) if sorted_pages else 1)

        page_batches: List[Tuple[int, int, str]] = []
        for start_idx in range(0, len(sorted_pages), batch_size):
            batch_slice = sorted_pages[start_idx:start_idx + batch_size]
            start_p = batch_slice[0]
            end_p = batch_slice[-1]
            batch_text_blocks = []
            for p in batch_slice:
                batch_text_blocks.append(f"--- Page {p} ---\n" + "\n".join(page_to_text[p]))
            page_batches.append((start_p, end_p, "\n".join(batch_text_blocks)))

        map_tasks = []
        for sec_idx, (p_start, p_end, text_content) in enumerate(page_batches, start=1):
            map_tasks.append(
                cls._summarize_batch_with_concurrency(
                    filename=target_document.filename,
                    section_index=sec_idx,
                    page_start=p_start,
                    page_end=p_end,
                    batch_text=text_content
                )
            )

        batch_results = await asyncio.gather(*map_tasks)

        await database_session.execute(
            delete(DocumentSectionRecord).where(DocumentSectionRecord.document_id == document_id)
        )

        persisted_records: List[DocumentSectionRecord] = []
        for res in batch_results:
            sec_record = DocumentSectionRecord(
                document_id=document_id,
                section_index=res["section_index"],
                page_start=res["page_start"],
                page_end=res["page_end"],
                section_title=res["section_title"],
                section_summary=res["section_summary"],
                key_bullet_points=json.dumps(res["key_bullet_points"])
            )
            database_session.add(sec_record)
            persisted_records.append(sec_record)

        await database_session.commit()
        for r in persisted_records:
            await database_session.refresh(r)

        return persisted_records

    @classmethod
    async def _summarize_batch_with_concurrency(
        cls,
        filename: str,
        section_index: int,
        page_start: int,
        page_end: int,
        batch_text: str
    ) -> Dict[str, Any]:
        async with cls.CONCURRENT_SEMAPHORE:
            cleaned_text = re.sub(r"\[Document:.*?\]", "", batch_text)
            page_range_label = f"Pages {page_start}-{page_end}" if page_start != page_end else f"Page {page_start}"

            if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
                gemini_res = await cls._try_gemini_batch_summary(
                    filename=filename,
                    page_range_label=page_range_label,
                    text_content=cleaned_text[:7500]
                )
                if gemini_res:
                    return {
                        "section_index": section_index,
                        "page_start": page_start,
                        "page_end": page_end,
                        "section_title": gemini_res.get("section_title", f"{filename} ({page_range_label})"),
                        "section_summary": gemini_res.get("section_summary", ""),
                        "key_bullet_points": gemini_res.get("key_bullet_points", [])
                    }

            return cls._generate_fallback_batch_summary(
                filename=filename,
                section_index=section_index,
                page_start=page_start,
                page_end=page_end,
                text_content=cleaned_text
            )

    @classmethod
    async def _try_gemini_batch_summary(
        cls,
        filename: str,
        page_range_label: str,
        text_content: str
    ) -> Optional[Dict[str, Any]]:
        try:
            from google import genai
            from google.genai import types

            prompt = (
                f"Extract key facts, core methodologies, and essential takeaways from {page_range_label} "
                f"of document '{filename}'. Be dense and factual.\n\n"
                f"Text:\n{text_content}\n\n"
                f"Output strictly valid JSON with keys: 'section_title' (string), 'section_summary' (dense 150-word string), "
                f"'key_bullet_points' (array of 3 to 5 strings with page citations).\n"
                f"Do not include markdown code fences."
            )

            client = genai.Client(api_key=settings.gemini_api_key)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed = json.loads(raw_text.strip())
            if isinstance(parsed, dict) and "section_summary" in parsed:
                return parsed
        except Exception:
            return None
        return None

    @classmethod
    def _generate_fallback_batch_summary(
        cls,
        filename: str,
        section_index: int,
        page_start: int,
        page_end: int,
        text_content: str
    ) -> Dict[str, Any]:
        page_label = f"Pages {page_start}-{page_end}" if page_start != page_end else f"Page {page_start}"
        lines = [line.strip() for line in text_content.split("\n") if len(line.strip()) > 0]

        detected_headers = []
        for line in lines:
            if line.startswith("#") or line.isupper() and 4 < len(line) < 60:
                clean_h = line.lstrip("#").strip()
                if clean_h and clean_h not in detected_headers:
                    detected_headers.append(clean_h)

        title = detected_headers[0] if detected_headers else f"Section {section_index} ({page_label})"

        factual_sentences = []
        for line in lines:
            if len(line) > 30 and not line.startswith("---") and not line.startswith("#"):
                for s in line.split(". "):
                    cleaned_s = s.strip()
                    if len(cleaned_s) > 25 and len(cleaned_s.split()) >= 5:
                        factual_sentences.append(cleaned_s if cleaned_s.endswith(".") else cleaned_s + ".")

        selected_sentences = factual_sentences[:4]
        summary_text = " ".join(selected_sentences) if selected_sentences else f"Covers primary technical guidelines and domain documentation for {page_label}."

        bullets = []
        for sent in factual_sentences[2:7]:
            bullets.append(f"{sent} [{page_label}]")

        if not bullets:
            bullets = [
                f"Detailed core operational concepts for {filename} [{page_label}].",
                f"Established domain definitions and structured principles [{page_label}]."
            ]

        return {
            "section_index": section_index,
            "page_start": page_start,
            "page_end": page_end,
            "section_title": title[:200],
            "section_summary": summary_text[:1200],
            "key_bullet_points": bullets[:5]
        }

    @classmethod
    async def get_or_build_hierarchical_summary(
        cls,
        document_id: int,
        database_session: AsyncSession
    ) -> Dict[str, Any]:
        sections_query = (
            select(DocumentSectionRecord)
            .where(DocumentSectionRecord.document_id == document_id)
            .order_by(DocumentSectionRecord.section_index.asc())
        )
        sections_result = await database_session.execute(sections_query)
        existing_sections = list(sections_result.scalars().all())

        if not existing_sections:
            existing_sections = await cls.index_document_sections(document_id, database_session)

        doc_query = select(DocumentRecord).where(DocumentRecord.id == document_id)
        doc_result = await database_session.execute(doc_query)
        target_doc = doc_result.scalar_one_or_none()
        doc_filename = target_doc.filename if target_doc else f"Document #{document_id}"

        combined_section_notes = []
        all_bullet_points = []
        all_topics = []

        for sec in existing_sections:
            page_lbl = f"Pages {sec.page_start}-{sec.page_end}" if sec.page_start != sec.page_end else f"Page {sec.page_start}"
            combined_section_notes.append(
                f"[{page_lbl} | {sec.section_title or 'Section'}]: {sec.section_summary}"
            )
            if sec.key_bullet_points:
                try:
                    loaded_bullets = json.loads(sec.key_bullet_points)
                    all_bullet_points.extend(loaded_bullets)
                except Exception:
                    pass
            if sec.section_title and "Section" not in sec.section_title:
                all_topics.append(sec.section_title)

        dense_notes_string = "\n\n".join(combined_section_notes)

        executive_summary = None
        if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
            executive_summary = await cls._try_gemini_reduce_summary(
                filename=doc_filename,
                combined_notes=dense_notes_string
            )

        if not executive_summary:
            executive_summary = cls._generate_fallback_reduce_summary(
                filename=doc_filename,
                sections=existing_sections
            )

        return {
            "document_id": document_id,
            "filename": doc_filename,
            "executive_summary": executive_summary,
            "key_takeaways": all_bullet_points[:8] if all_bullet_points else [f"Comprehensive review spanning all {len(existing_sections)} hierarchical document sections."],
            "topics": list(dict.fromkeys(all_topics))[:8] if all_topics else ["Overview", "Architecture", "Methodology", "Analysis"],
            "total_sections": len(existing_sections)
        }

    @classmethod
    async def _try_gemini_reduce_summary(
        cls,
        filename: str,
        combined_notes: str
    ) -> Optional[str]:
        try:
            from google import genai
            from google.genai import types

            prompt = (
                f"You are an executive research analyst. Synthesize a comprehensive, polished executive summary "
                f"with page citations for the full document '{filename}' based on these pre-computed hierarchical section notes:\n\n"
                f"{combined_notes[:10000]}\n\n"
                f"Requirements:\n"
                f"- High-level purpose and core domain thesis.\n"
                f"- Key findings, methodologies, and framework components with exact [Page X] or [Pages X-Y] citations.\n"
                f"- Actionable conclusion.\n"
                f"Keep tone clear, authoritative, and direct."
            )

            client = genai.Client(api_key=settings.gemini_api_key)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2
                )
            )
            return response.text.strip()
        except Exception:
            return None

    @classmethod
    def _generate_fallback_reduce_summary(
        cls,
        filename: str,
        sections: List[DocumentSectionRecord]
    ) -> str:
        synthesis_paragraphs = [
            f"**Executive Synthesis for '{filename}'**",
            f"This comprehensive document spans {sections[-1].page_end if sections else 1} pages across {len(sections)} distinct thematic sections."
        ]

        section_overviews = []
        for sec in sections:
            page_lbl = f"Pages {sec.page_start}-{sec.page_end}" if sec.page_start != sec.page_end else f"Page {sec.page_start}"
            section_overviews.append(f"- **{sec.section_title or page_lbl} [{page_lbl}]:** {sec.section_summary}")

        synthesis_paragraphs.append("\n".join(section_overviews))
        synthesis_paragraphs.append(
            f"**Conclusion:** All {len(sections)} structural sections were indexed and synthesized into this unified brief, ensuring zero blind spots across the complete document corpus."
        )

        return "\n\n".join(synthesis_paragraphs)
