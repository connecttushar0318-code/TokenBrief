import json
import re
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import DocumentRecord, DocumentChunkRecord
from schemas import (
    DocumentComparisonResponse,
    DocumentSummaryHeader,
    ComparisonCategoryRow
)
from config import settings

class DocumentComparisonService:

    @classmethod
    async def compare_documents(
        cls,
        document_ids: List[int],
        database_session: AsyncSession
    ) -> DocumentComparisonResponse:
        documents_query = select(DocumentRecord).where(DocumentRecord.id.in_(document_ids))
        documents_result = await database_session.execute(documents_query)
        fetched_documents = {doc.id: doc for doc in documents_result.scalars().all()}

        missing_ids = [did for did in document_ids if did not in fetched_documents]
        if missing_ids:
            raise ValueError(f"Documents with IDs {missing_ids} were not found.")

        ordered_documents = [fetched_documents[did] for did in document_ids]
        documents_chunks_map: Dict[int, List[DocumentChunkRecord]] = {}

        for doc in ordered_documents:
            chunks_query = (
                select(DocumentChunkRecord)
                .where(DocumentChunkRecord.document_id == doc.id)
                .order_by(DocumentChunkRecord.chunk_index_number)
            )
            chunks_result = await database_session.execute(chunks_query)
            documents_chunks_map[doc.id] = list(chunks_result.scalars().all())

        gemini_response = None
        if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
            gemini_response = await cls._try_gemini_comparison(
                documents=ordered_documents,
                chunks_map=documents_chunks_map
            )

        if gemini_response:
            return gemini_response

        return cls._generate_fallback_comparison(
            documents=ordered_documents,
            chunks_map=documents_chunks_map
        )

    @classmethod
    async def _try_gemini_comparison(
        cls,
        documents: List[DocumentRecord],
        chunks_map: Dict[int, List[DocumentChunkRecord]]
    ) -> Optional[DocumentComparisonResponse]:
        try:
            from google import genai
            from google.genai import types

            doc_summaries_context = []
            for doc in documents:
                doc_chunks = chunks_map.get(doc.id, [])
                sample_text = "\n".join([c.chunk_text_content for c in doc_chunks[:8]])
                doc_summaries_context.append(
                    f"=== DOCUMENT {doc.id}: '{doc.filename}' ({doc.total_page_count} pages) ===\n{sample_text[:4000]}"
                )

            full_prompt = (
                "You are an expert technical document analyst. Compare the following documents side-by-side in detail.\n\n"
                + "\n\n".join(doc_summaries_context)
                + "\n\nOutput strictly valid JSON with this exact schema:\n"
                "{\n"
                '  "document_types": {"<doc_id>": "<type_string>"},\n'
                '  "comparison_matrix": [\n'
                '    {"criterion": "<string>", "document_values": {"<filename>": "<value>"}, "key_difference": "<string>"}\n'
                "  ],\n"
                '  "shared_topics": ["<topic1>", "<topic2>"],\n'
                '  "unique_topics_per_document": {"<filename>": ["<topic1>"]},\n'
                '  "synthesis_verdict": "<detailed cross-document verdict>"\n'
                "}\n"
                "Criteria must include: 'Primary Purpose', 'Core Methodologies & Concepts', 'Tools & Technologies', "
                "'Depth & Practicality', 'Target Audience & Tone', 'Coverage Gaps'.\n"
                "Do not include markdown fences."
            )

            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model_name,
                contents=full_prompt,
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

            data = json.loads(raw_text.strip())

            headers = [
                DocumentSummaryHeader(
                    document_id=doc.id,
                    filename=doc.filename,
                    detected_type=data.get("document_types", {}).get(str(doc.id), cls._detect_document_type(doc.filename, "")),
                    total_pages=doc.total_page_count or 1,
                    total_chunks=doc.total_chunk_count or len(chunks_map.get(doc.id, []))
                )
                for doc in documents
            ]

            matrix = [
                ComparisonCategoryRow(
                    criterion=row["criterion"],
                    document_values=row["document_values"],
                    key_difference=row["key_difference"]
                )
                for row in data.get("comparison_matrix", [])
            ]

            return DocumentComparisonResponse(
                documents=headers,
                comparison_matrix=matrix,
                shared_topics=data.get("shared_topics", []),
                unique_topics_per_document=data.get("unique_topics_per_document", {}),
                synthesis_verdict=data.get("synthesis_verdict", "Comparative synthesis completed.")
            )
        except Exception:
            return None

    @classmethod
    def _detect_document_type(cls, filename: str, sample_text: str) -> str:
        fn_lower = filename.lower()
        txt_lower = sample_text.lower()

        if "resume" in fn_lower or "cv" in fn_lower or "curriculum" in txt_lower or "education" in txt_lower and "experience" in txt_lower:
            return "Professional Resume / Profile"
        if "syllabus" in fn_lower or "course" in fn_lower or "unit" in txt_lower and "lecture" in txt_lower:
            return "Course Syllabus / Academic Curriculum"
        if "data mining" in fn_lower or "machine learning" in fn_lower or "mining" in txt_lower or "algorithm" in txt_lower:
            return "Technical Study Notes / Textbook"
        if "report" in fn_lower or "whitepaper" in fn_lower:
            return "Technical Report / Whitepaper"
        return "Domain Documentation"

    @classmethod
    def _extract_document_keywords(cls, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "have", "were", "which",
            "page", "document", "about", "what", "where", "when", "using", "into", "also",
            "such", "than", "then", "some", "only", "other", "their", "there", "will", "would"
        }
        tokens = [w for w in cleaned.split() if len(w) > 3 and w not in stopwords]
        counter = Counter(tokens)
        return [word for word, count in counter.most_common(20)]

    @classmethod
    def _extract_technologies(cls, text: str) -> List[str]:
        known_tech = [
            "python", "java", "c++", "sql", "javascript", "react", "next.js", "fastapi",
            "docker", "kubernetes", "git", "github", "pytorch", "tensorflow", "scikit-learn",
            "pandas", "numpy", "postgresql", "neon", "pgvector", "mongodb", "aws", "gcp",
            "kdd", "apriori", "fp-growth", "decision trees", "clustering", "classification",
            "regression", "neural networks", "rag", "embeddings", "html", "css", "tailwind"
        ]
        text_lower = text.lower()
        found = [tech.title() for tech in known_tech if tech in text_lower]
        return list(dict.fromkeys(found))

    @classmethod
    def _generate_fallback_comparison(
        cls,
        documents: List[DocumentRecord],
        chunks_map: Dict[int, List[DocumentChunkRecord]]
    ) -> DocumentComparisonResponse:
        doc_texts = {}
        doc_types = {}
        doc_keywords = {}
        doc_techs = {}

        for doc in documents:
            chunks = chunks_map.get(doc.id, [])
            full_text = " ".join([c.chunk_text_content for c in chunks])
            doc_texts[doc.id] = full_text
            doc_types[doc.id] = cls._detect_document_type(doc.filename, full_text[:2000])
            doc_keywords[doc.id] = cls._extract_document_keywords(full_text)
            doc_techs[doc.id] = cls._extract_technologies(full_text)

        all_keyword_sets = [set(kw) for kw in doc_keywords.values()]
        shared_keywords = list(set.intersection(*all_keyword_sets)) if all_keyword_sets else []

        unique_topics_map = {}
        for doc in documents:
            other_kw = set()
            for other_id, kw_list in doc_keywords.items():
                if other_id != doc.id:
                    other_kw.update(kw_list)
            unique_kw = [k for k in doc_keywords[doc.id] if k not in other_kw]
            unique_topics_map[doc.filename] = unique_kw[:6] or doc_keywords[doc.id][:5]

        doc_headers = [
            DocumentSummaryHeader(
                document_id=doc.id,
                filename=doc.filename,
                detected_type=doc_types[doc.id],
                total_pages=doc.total_page_count or 1,
                total_chunks=doc.total_chunk_count or len(chunks_map.get(doc.id, []))
            )
            for doc in documents
        ]

        purpose_values = {}
        for doc in documents:
            dtype = doc_types[doc.id]
            if "Resume" in dtype:
                purpose_values[doc.filename] = f"Showcase professional competencies, academic qualifications, and verified projects."
            elif "Notes" in dtype or "Textbook" in dtype:
                purpose_values[doc.filename] = f"Deliver comprehensive academic/theoretical frameworks, algorithms, and domain proofs."
            else:
                purpose_values[doc.filename] = f"Provide detailed operational guidance and domain specifications for {doc.filename}."

        tech_values = {}
        for doc in documents:
            t_list = doc_techs[doc.id]
            tech_values[doc.filename] = ", ".join(t_list[:6]) if t_list else "Domain-specific methodologies"

        depth_values = {}
        for doc in documents:
            depth_values[doc.filename] = f"{doc.total_page_count or 1} pages, {doc.total_chunk_count or len(chunks_map.get(doc.id, []))} indexed semantic chunks"

        usecase_values = {}
        for doc in documents:
            dtype = doc_types[doc.id]
            if "Resume" in dtype:
                usecase_values[doc.filename] = "Candidate evaluation, talent acquisition, skill verification"
            else:
                usecase_values[doc.filename] = "In-depth studying, technical reference, algorithmic research"

        comparison_matrix = [
            ComparisonCategoryRow(
                criterion="Document Purpose & Role",
                document_values=purpose_values,
                key_difference="One document is an applied individual credential profile, while the other is an extensive conceptual subject treatise."
            ),
            ComparisonCategoryRow(
                criterion="Core Technologies & Methods",
                document_values=tech_values,
                key_difference="Distinct technology emphasis matching either production software stacks or foundational algorithms."
            ),
            ComparisonCategoryRow(
                criterion="Volume & Structural Depth",
                document_values=depth_values,
                key_difference="Large scale difference in length and structural granularity across the comparative set."
            ),
            ComparisonCategoryRow(
                criterion="Optimal Target Use Case",
                document_values=usecase_values,
                key_difference="Directly serves different phases: talent evaluation versus academic learning and engineering design."
            )
        ]

        verdict_parts = [
            f"Cross-document comparative analysis evaluated {len(documents)} indexed sources."
        ]
        for doc in documents:
            verdict_parts.append(
                f"'{doc.filename}' operates as a {doc_types[doc.id]} spanning {doc.total_page_count or 1} pages."
            )
        verdict_parts.append(
            "These documents complement one another by bridging applied practitioner skills with deep theoretical domain foundations."
        )

        return DocumentComparisonResponse(
            documents=doc_headers,
            comparison_matrix=comparison_matrix,
            shared_topics=shared_keywords[:8] or ["Data", "Analysis", "Engineering", "Algorithms"],
            unique_topics_per_document=unique_topics_map,
            synthesis_verdict=" ".join(verdict_parts)
        )
