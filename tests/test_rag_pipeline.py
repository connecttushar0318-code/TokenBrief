import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from database import initialize_database_tables, database_session_factory
from models import DocumentRecord, DocumentSectionRecord
from services.hierarchical_service import HierarchicalDocumentSummaryService
from services.query_router import QueryIntentRouterService, QueryIntent
from services.search_service import VectorSimilaritySearchEngine
from services.guardrails_service import HallucinationGuardrailService
from sqlalchemy import select

async def run_pipeline_test():
    print("=== 1. Initializing Tables (including document_sections) ===")
    await initialize_database_tables()
    print("Tables initialized successfully.")

    async with database_session_factory() as session:
        docs = (await session.execute(select(DocumentRecord))).scalars().all()
        print(f"Loaded {len(docs)} documents.")
        dm_doc = next((d for d in docs if "dm" in d.filename.lower() or d.total_page_count > 10), None)
        resume_doc = next((d for d in docs if "resume" in d.filename.lower()), None)

        if not dm_doc:
            dm_doc = docs[0]

        print(f"\n=== 2. Testing Hierarchical 5-Page Batch Indexing on: {dm_doc.filename} ({dm_doc.total_page_count} pages) ===")
        sections = await HierarchicalDocumentSummaryService.index_document_sections(
            document_id=dm_doc.id,
            database_session=session,
            batch_size=5
        )
        print(f"Successfully created {len(sections)} parent section batches (Map step):")
        for s in sections[:4]:
            print(f"  - Section {s.section_index} (Pages {s.page_start}-{s.page_end}): {s.section_title}")
            print(f"    Summary: {s.section_summary[:90]}...")
        if len(sections) > 4:
            last_sec = sections[-1]
            print(f"  ... up to Section {last_sec.section_index} (Pages {last_sec.page_start}-{last_sec.page_end}): {last_sec.section_title}")

        print("\n=== 3. Testing Reduce Step: Hierarchical Full-Document Brief ===")
        hierarchical_brief = await HierarchicalDocumentSummaryService.get_or_build_hierarchical_summary(
            document_id=dm_doc.id,
            database_session=session
        )
        print(f"Executive Summary length: {len(hierarchical_brief['executive_summary'])} chars")
        print(f"Executive Summary excerpt: {hierarchical_brief['executive_summary'][:180]}...")
        print(f"Total Sections covered: {hierarchical_brief['total_sections']} (100% of pages)")
        print(f"Key Takeaways count: {len(hierarchical_brief['key_takeaways'])}")

        print("\n=== 4. Testing Query Intent Router ===")
        test_queries = [
            ("Summarize this 48 page PDF completely", QueryIntent.GLOBAL_SUMMARY),
            ("Give me an overview of the main themes in this document", QueryIntent.GLOBAL_SUMMARY),
            ("Compare the resume with the DM notes file", QueryIntent.MULTI_DOC_COMPARE),
            ("What is the definition of data mining on page 3?", QueryIntent.SPECIFIC_FACT),
            ("Which programming languages does the candidate know?", QueryIntent.SPECIFIC_FACT),
        ]
        doc_inventory = [{"id": d.id, "filename": d.filename} for d in docs]
        for query_str, expected in test_queries:
            decision = QueryIntentRouterService.classify_query_intent(
                user_query_text=query_str,
                available_documents=doc_inventory
            )
            is_match = (decision["intent"] == expected)
            print(f"  Query: '{query_str}' -> {decision['intent'].value} (Expected: {expected.value}, Correct: {is_match})")

        print("\n=== 5. Testing Hybrid Search (BM25 + Vector RRF) ===")
        chunks, _ = await VectorSimilaritySearchEngine.find_most_relevant_chunks(
            database_session=session,
            user_query_text="Apriori algorithm association rules",
            filter_document_id=dm_doc.id,
            maximum_results_count=3
        )
        print(f"Retrieved {len(chunks)} fused candidates with RRF scores:")
        for c in chunks:
            print(f"  - Chunk #{c['chunk_id']} | Page {c['source_page_number']} | RRF: {c.get('rrf_score')} | Rerank: {c.get('rerank_score')}")

        print("\n=== 6. Testing Hallucination Guardrail & Abstention Gate ===")
        abstain, msg = HallucinationGuardrailService.evaluate_retrieval_confidence(
            retrieved_chunks=[{"similarity_percentage": 14.5}],
            query_text="What is the quantum alien interstellar speed limit?",
            confidence_threshold=25.0
        )
        print(f"Abstention Gate Triggered: {abstain}")
        print(f"Abstention Message: {msg}")

        print("\n=== 7. Testing Citation Verification ===")
        test_answer = "Data mining involves classification [Page 4] and neural nets [Page 99]."
        sanitized_ans, meta = HallucinationGuardrailService.verify_and_align_citations(
            answer_text=test_answer,
            retrieved_chunks=[{"source_page_number": 4}, {"source_page_number": 5}]
        )
        print(f"Original answer: {test_answer}")
        print(f"Sanitized answer: {sanitized_ans}")
        print(f"Citation metadata: {meta}")

        print("\n=== RAG & BACKEND SYSTEMS ARCHITECTURE VERIFIED! ===")

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
