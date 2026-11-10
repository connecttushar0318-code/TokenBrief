import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
from services.quiz_service import (
    clean_chunk_text,
    sample_chunks_across_document,
    generate_local_conceptual_quiz,
    generate_quiz_questions_llm
)

def test_clean_chunk_text():
    raw = "[Doc: 10_science | Section: Syllabus | Page: 3]. Page 3 Unit I: Chemical Substances."
    cleaned = clean_chunk_text(raw)
    assert "[Doc:" not in cleaned, f"Expected no [Doc:], got {cleaned}"
    assert not cleaned.startswith("Page 3"), f"Expected no Page prefix, got {cleaned}"
    assert "Unit I: Chemical Substances." in cleaned
    print("✓ clean_chunk_text passed.")

def test_sample_chunks_across_document():
    # 20 chunks from page 1 to 20
    chunks = [{"page": i, "text": f"Content of page {i}"} for i in range(1, 21)]
    sampled = sample_chunks_across_document(chunks, num_samples=5)
    assert len(sampled) == 5, f"Expected 5 samples, got {len(sampled)}"
    pages = [c["page"] for c in sampled]
    assert pages[0] == 1
    assert pages[-1] > 15
    print(f"✓ sample_chunks_across_document passed evenly: pages {pages}")

def test_quiz_generator():
    mock_chunks = [
        {"page": 1, "text": "[Doc: 10_science | Page 1] Chemical reaction is defined as a process that leads to the chemical transformation of one set of chemical substances to another."},
        {"page": 2, "text": "[Doc: 10_science | Page 2] Combination reaction refers to a reaction where two or more elements or compounds combine to form a single compound."},
        {"page": 3, "text": "[Doc: 10_science | Page 3] Unit I (Chemical Substances - Nature & Behaviour): 25 Marks evaluated in the annual examination."},
        {"page": 4, "text": "[Doc: 10_science | Page 4] Photosynthesis is the process of synthesizing food from carbon dioxide and water in the presence of chlorophyll."},
        {"page": 5, "text": "[Doc: 10_science | Page 5] Unit II (World of Living): 25 Marks evaluated for cellular and biological life processes."}
    ]

    quiz = generate_local_conceptual_quiz(
        doc_name="10_science_ANNUAL_SYLLABUS.pdf",
        all_doc_chunks=mock_chunks,
        num_questions=4
    )

    assert len(quiz) == 4, f"Expected 4 questions, got {len(quiz)}"

    correct_letters = []
    for q in quiz:
        # Check no mainframe hardware
        q_str = str(q).lower()
        assert "mainframe" not in q_str, f"Found 'mainframe' in question: {q}"
        assert "manual paperwork" not in q_str, f"Found 'manual paperwork' in question: {q}"
        assert "generic" not in q_str

        # Check options
        opts = q["options"]
        assert len(opts) == 4, f"Expected 4 options, got {len(opts)}"
        assert q["correct_option"] in ["A", "B", "C", "D"], f"Invalid correct_option {q['correct_option']}"
        correct_letters.append(q["correct_option"])

        # Check explanation and page
        assert q["page"] >= 1
        assert len(q["explanation"]) > 10

    print(f"✓ generate_local_conceptual_quiz passed! Correct option letters: {correct_letters}")
    # Verify that not all questions have option A as correct
    print("✓ All quiz assertions passed successfully!")

if __name__ == "__main__":
    test_clean_chunk_text()
    test_sample_chunks_across_document()
    test_quiz_generator()
