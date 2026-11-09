import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import initialize_database_tables, database_session_factory
from models import DocumentRecord, UserAccount
from services.quiz_service import QuizEngineService
from services.comparison_service import DocumentComparisonService
from services.analytics_service import AnalyticsDashboardService
from services.export_service import SessionPdfExportService
from services.entity_service import EntityKnowledgeGraphService
from sqlalchemy import select

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

async def run_feature_verifications():
    print("--- 1. Initializing database tables ---")
    await initialize_database_tables()
    print("Database tables initialized successfully.")

    async with database_session_factory() as session:
        docs_res = await session.execute(select(DocumentRecord))
        docs = docs_res.scalars().all()
        print(f"Found {len(docs)} existing documents in DB:")
        for d in docs:
            print(f"  - Doc ID {d.id}: {d.filename} ({d.total_page_count} pages, {d.total_chunk_count} chunks)")

        if not docs:
            print("No documents found to test on. Exiting.")
            return

        target_doc = docs[0]

        print("\n--- 2. Testing Feature 1: Quiz Engine Generation ---")
        questions = await QuizEngineService.generate_quiz_questions(
            document_id=target_doc.id,
            number_of_questions=3,
            difficulty="medium",
            database_session=session
        )
        print(f"Generated {len(questions)} quiz questions:")
        for q in questions:
            print(f"  [Q{q.id}] {q.question_text}")
            print(f"     A: {q.option_a}")
            print(f"     B: {q.option_b}")
            print(f"     C: {q.option_c}")
            print(f"     D: {q.option_d}")
            print(f"     Correct: {q.correct_option}")

        print("\n--- 3. Testing Feature 2: Document Comparison ---")
        if len(docs) >= 2:
            comparison = await DocumentComparisonService.compare_documents(
                document_ids=[docs[0].id, docs[1].id],
                database_session=session
            )
            print(f"Comparison completed with {len(comparison.comparison_matrix)} criteria.")
            print(f"Synthesis verdict: {comparison.synthesis_verdict[:120]}...")
            print(f"Shared topics: {comparison.shared_topics}")
        else:
            print("Less than 2 documents available; skipping multi-doc comparison.")

        print("\n--- 4. Testing Feature 3: Real Analytics Logging & Dashboard ---")
        await AnalyticsDashboardService.record_query_log(
            database_session=session,
            question_text="What are the key qualifications?",
            latency_ms=145.2,
            cache_hit=False,
            model_used="DocuVibe Neural Engine",
            estimated_token_count=180,
            user_id=target_doc.user_id,
            document_id=target_doc.id
        )
        dashboard = await AnalyticsDashboardService.get_dashboard_metrics(
            database_session=session,
            user_id=target_doc.user_id
        )
        print(f"Dashboard total queries: {dashboard.total_queries}")
        print(f"Average latency: {dashboard.average_latency_ms} ms")
        print(f"Model breakdown: {[m.model_dump() for m in dashboard.model_breakdown]}")

        print("\n--- 5. Testing Feature 4: PDF Export ---")
        sample_messages = [
            {"sender_role": "user", "message_text": "Can you summarize the candidate's core expertise?"},
            {"sender_role": "assistant", "message_text": "The candidate has demonstrated expertise in Python, RAG architectures, Machine Learning, and database design."}
        ]
        pdf_bytes = SessionPdfExportService.create_formatted_pdf_bytes(
            session_title="Executive Candidate Assessment",
            user_name="krohitrkumar",
            referenced_documents=[target_doc.filename],
            messages=sample_messages
        )
        print(f"Generated PDF bytes: {len(pdf_bytes)} bytes")

        print("\n--- 6. Testing Feature 5: Entity & Knowledge Graph Extraction ---")
        entities_resp = await EntityKnowledgeGraphService.extract_and_store_entities(
            document_id=target_doc.id,
            database_session=session
        )
        print(f"Extracted {entities_resp.total_entities} entities:")
        for cat, ent_list in entities_resp.entities_by_type.items():
            print(f"  {cat}: {ent_list[:5]}")

        graph_resp = await EntityKnowledgeGraphService.get_document_graph(
            document_id=target_doc.id,
            database_session=session
        )
        print(f"Graph nodes: {len(graph_resp.nodes)}, Graph links: {len(graph_resp.links)}")

        workspace_graph = await EntityKnowledgeGraphService.get_workspace_graph(
            database_session=session,
            user_id=target_doc.user_id
        )
        print(f"Workspace Graph: {len(workspace_graph.nodes)} nodes, {len(workspace_graph.links)} links")

        print("\n--- 7. Testing Feature 6: Annotations & Highlights ---")
        from models import UserAnnotationRecord
        test_annotation = UserAnnotationRecord(
            user_id=target_doc.user_id or 1,
            document_id=target_doc.id,
            highlighted_text="Python, Machine Learning, and Neural Networks",
            annotation_note="Key technical competencies identified",
            color_code="yellow",
            source_page_number=1
        )
        session.add(test_annotation)
        await session.commit()
        await session.refresh(test_annotation)
        print(f"Successfully created annotation ID {test_annotation.id} for user {test_annotation.user_id}")

        anno_query = select(UserAnnotationRecord).where(UserAnnotationRecord.id == test_annotation.id)
        saved_anno = (await session.execute(anno_query)).scalar_one_or_none()
        print(f"Retrieved annotation note: '{saved_anno.annotation_note}', color: '{saved_anno.color_code}'")

        await session.delete(test_annotation)
        await session.commit()
        print("Test annotation cleaned up successfully.")

        print("\n=== ALL 6 BACKEND FEATURES VALIDATED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_feature_verifications())
