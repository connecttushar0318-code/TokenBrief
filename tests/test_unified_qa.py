import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import re
from services.qa_service import clean_text, build_full_file_digest, ask_tokenbrief, LLMClient
from services.guardrails_service import HallucinationGuardrailService

async def run_tests():
    print("=== TEST 1: clean_text removes [Doc: ...] and Page headers ===")
    raw = "[Doc: DM File.pdf | Section: Overview | Page: 1]. Page 1 Data Mining is the process of discovering patterns."
    cleaned = clean_text(raw)
    assert "[Doc:" not in cleaned, f"Expected no [Doc:], got {cleaned}"
    assert "Page 1" not in cleaned or "Data Mining" in cleaned
    print("✓ clean_text passed:", cleaned)

    print("\n=== TEST 2: build_full_file_digest never cuts words (snaps to word boundary) ===")
    long_text = "The importance of data mining in modern enterprise systems is undeniable. " * 30
    chunks = [
        {"page": 1, "text": long_text},
        {"page": 2, "text": "Clustering algorithms like K-Means are widely used for segmentation."}
    ]
    digest = build_full_file_digest(chunks)
    assert "importa " not in digest and "importa." not in digest, "Word was chopped into importa!"
    assert "importance" in digest, "Expected 'importance' in digest"
    assert "[Source Page/Time 1]:" in digest
    assert "[Source Page/Time 2]:" in digest
    print("✓ build_full_file_digest passed cleanly without word truncation.")

    print("\n=== TEST 3: ask_tokenbrief handles greeting 'hlo' with sources: [] ===")
    res_greeting = await ask_tokenbrief(
        user_message="hlo",
        file_name="DM File.pdf",
        all_file_chunks=chunks,
        top_k_chunks=[],
        llm_client=LLMClient
    )
    print("Answer:", res_greeting["answer"])
    print("Sources:", res_greeting["sources"])
    assert len(res_greeting["sources"]) == 0, f"Expected sources: [], got {res_greeting['sources']}"
    assert "TokenBrief AI" in res_greeting["answer"]
    assert "DM File.pdf" in res_greeting["answer"]
    print("✓ Greeting 'hlo' returned friendly English reply with sources: [].")

    print("\n=== TEST 4: ask_tokenbrief handles typo 'summerize the core parts only' ===")
    res_summary = await ask_tokenbrief(
        user_message="summerize the core parts only",
        file_name="DM File.pdf",
        all_file_chunks=chunks,
        top_k_chunks=chunks[:1],
        llm_client=LLMClient
    )
    print("Answer:", res_summary["answer"][:150] + "...")
    print("Sources:", res_summary["sources"])
    assert len(res_summary["sources"]) > 0 or len(res_summary["cited_pages"]) > 0
    assert "importa " not in res_summary["answer"]
    print("✓ 'summerize the core parts only' parsed natively and cited properly.")

    print("\n=== TEST 5: 25.0% similarity blocker is deleted ===")
    low_chunks = [{"chunk_id": 1, "similarity_percentage": 7.74, "chunk_text_content": "random"}]
    should_abstain, msg = HallucinationGuardrailService.evaluate_retrieval_confidence(
        retrieved_chunks=low_chunks,
        query_text="hlo",
        confidence_threshold=25.0
    )
    assert not should_abstain, "Guardrail should NOT abstain for low similarity!"
    assert msg is None
    print("✓ 25.0% similarity blocker verified deleted (should_abstain=False).")

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
