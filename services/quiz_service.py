import json
import re
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete
from models import (
    QuizQuestionRecord,
    QuizAttemptRecord,
    QuizAnswerRecord,
    DocumentRecord,
    DocumentChunkRecord
)
from config import settings
from services.qa_service import LLMClient


def clean_chunk_text(raw_text: str) -> str:
    """Removes leaked internal tags like '[Doc: ... | Section: ... | Page: 1].'"""
    text = re.sub(r"^\[Doc:.*?\]\.?\s*", "", raw_text, flags=re.DOTALL)
    text = re.sub(r"^Page\s+\d+\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def sample_chunks_across_document(all_chunks: List[Dict], num_samples: int = 8) -> List[Dict]:
    """
    Picks chunks evenly spread across all pages of the PDF (1 to 50+ pages)
    so the quiz covers the whole document rather than just Page 1.
    """
    if not all_chunks:
        return []
    if len(all_chunks) <= num_samples:
        return all_chunks

    step = len(all_chunks) / num_samples
    return [all_chunks[int(i * step)] for i in range(num_samples)]


def generate_local_conceptual_quiz(
    doc_name: str,
    all_doc_chunks: List[Dict[str, Any]],
    num_questions: int = 5,
    difficulty: str = "medium"
) -> List[Dict[str, Any]]:
    """
    Generates genuine, high-quality domain-specific MCQs directly from document text
    when external LLM is offline or unconfigured. Never uses hardcoded mainframe strings.
    """
    sampled_chunks = sample_chunks_across_document(all_doc_chunks, num_samples=max(12, num_questions * 2))

    fact_candidates = []
    all_terms = []

    def_regex = re.compile(
        r"([A-Z][a-zA-Z0-9\s\-]{2,40})\s+(?:is defined as|refers to|is the process of|consists of|deals with|means|is characterized by)\s+([^\.\n]+)\.",
        re.IGNORECASE
    )
    unit_regex = re.compile(
        r"((?:Unit|Chapter|Section|Practical|Experiment|Module|Marks|Topic)\s+[^\.\n:]{3,50}[:\-]?\s+[^\.\n]+)\.",
        re.IGNORECASE
    )
    bullet_regex = re.compile(r"(?:•|\*|-|\d+\.)\s+([A-Z][^\.\n]{20,120}\.)")

    for chk in sampled_chunks:
        page_num = chk.get("page", 1)
        text = clean_chunk_text(chk.get("text", ""))
        if len(text) < 40:
            continue

        for match in def_regex.finditer(text):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if len(term) > 3 and len(definition) > 15:
                fact_candidates.append({
                    "type": "definition",
                    "term": term,
                    "answer": definition[:110],
                    "page": page_num,
                })
                all_terms.append(term)

        for match in unit_regex.finditer(text):
            sentence = match.group(1).strip()
            if len(sentence) > 25:
                fact_candidates.append({
                    "type": "topic",
                    "sentence": sentence[:120],
                    "page": page_num,
                })

        for match in bullet_regex.finditer(text):
            statement = match.group(1).strip()
            if len(statement) > 30 and not statement.startswith("Page"):
                fact_candidates.append({
                    "type": "statement",
                    "sentence": statement[:120],
                    "page": page_num,
                })

    distractor_pool = list(set(
        all_terms +
        [c.get("answer", "") for c in fact_candidates if c.get("answer")] +
        [c.get("sentence", "") for c in fact_candidates if c.get("sentence")]
    ))

    raw_questions = []

    for item in fact_candidates:
        if len(raw_questions) >= num_questions:
            break

        page_num = item["page"]

        if item["type"] == "definition":
            question_text = f"According to '{doc_name}', what is {item['term']}?"
            correct_ans = item["answer"]
            other_options = [d for d in distractor_pool if d != correct_ans and len(d) > 10 and d != item["term"]]
            if len(other_options) < 3:
                other_options.extend([
                    f"A secondary procedural step detailed in subsequent chapters",
                    f"A diagnostic metric reserved for non-standard evaluations",
                    f"A supplementary reference guideline not covered in this unit"
                ])
            wrong_answers = random.sample(other_options, 3)
            explanation = f"Page {page_num} states that {item['term']} is: '{correct_ans}'."

        elif item["type"] == "topic":
            question_text = f"Which curriculum or domain specification is outlined on Page {page_num}?"
            correct_ans = item["sentence"]
            other_options = [d for d in distractor_pool if d != correct_ans and len(d) > 15]
            if len(other_options) < 3:
                other_options.extend([
                    "An optional supplementary seminar requirement",
                    "A non-examinable reference curriculum framework",
                    "A preparatory module scheduled for subsequent terms"
                ])
            wrong_answers = random.sample(other_options, 3)
            explanation = f"Page {page_num} explicitly specifies: '{correct_ans}'."

        else:
            question_text = f"Which key guideline or finding is confirmed on Page {page_num} of {doc_name}?"
            correct_ans = item["sentence"]
            other_options = [d for d in distractor_pool if d != correct_ans and len(d) > 15]
            if len(other_options) < 3:
                other_options.extend([
                    "The complete exclusion of practical laboratory testing",
                    "A discretionary exception permitted only under external audit",
                    "A historical convention prior to current standardisation"
                ])
            wrong_answers = random.sample(other_options, 3)
            explanation = f"Document context on Page {page_num} confirms: '{correct_ans}'."

        raw_questions.append({
            "question": question_text,
            "correct_answer": correct_ans,
            "wrong_answers": wrong_answers,
            "page": page_num,
            "explanation": explanation
        })

    while len(raw_questions) < num_questions and sampled_chunks:
        chk = random.choice(sampled_chunks)
        page_num = chk.get("page", 1)
        cleaned = clean_chunk_text(chk.get("text", ""))
        sentences = [s.strip() for s in cleaned.split(".") if len(s.strip()) > 35]
        if sentences:
            chosen = sentences[0] + "."
            distractors = [
                f"An unverified theoretical assumption omitted from the core text of {doc_name}",
                f"A discontinued prerequisite from previous curriculum iterations",
                f"An external third-party protocol not referenced in this document"
            ]
            raw_questions.append({
                "question": f"Which principle is directly established on Page {page_num} of {doc_name}?",
                "correct_answer": chosen,
                "wrong_answers": distractors,
                "page": page_num,
                "explanation": f"Page {page_num} confirms the principle: '{chosen}'."
            })
        else:
            break

    formatted_quiz = []
    option_labels = ["A", "B", "C", "D"]

    for idx, q in enumerate(raw_questions[:num_questions], start=1):
        correct_text = q["correct_answer"].strip()
        distractors = [w.strip() for w in q["wrong_answers"][:3]]
        all_options = [correct_text] + distractors
        random.shuffle(all_options)

        correct_index = all_options.index(correct_text)
        correct_letter = option_labels[correct_index]

        formatted_quiz.append({
            "id": idx,
            "question": q["question"].strip(),
            "page": int(q.get("page", 1)),
            "options": {
                "A": all_options[0],
                "B": all_options[1],
                "C": all_options[2],
                "D": all_options[3],
            },
            "correct_option": correct_letter,
            "correct_index": correct_index,
            "explanation": q.get("explanation", "")
        })

    return formatted_quiz


async def generate_quiz_questions_llm(
    doc_name: str,
    all_doc_chunks: List[Dict[str, Any]],
    num_questions: int = 5,
    difficulty: str = "medium",
    llm_client = None
) -> List[Dict[str, Any]]:
    """
    Generates real conceptual MCQs with plausible same-topic distractors,
    shuffled option positions (A/B/C/D), explanations, and exact page citations.
    """
    sampled_chunks = sample_chunks_across_document(all_doc_chunks, num_samples=max(8, num_questions * 2))

    context_blocks = []
    for c in sampled_chunks:
        page_num = c.get("page", 1)
        cleaned = clean_chunk_text(c.get("text", ""))
        if len(cleaned) > 50:
            context_blocks.append(f"[Page {page_num}]: {cleaned}")

    document_context = "\n\n".join(context_blocks)

    if not llm_client:
        llm_client = LLMClient

    prompt = f"""You are an expert examiner creating an interactive quiz for the document "{doc_name}".
Based ONLY on the document excerpts below, generate {num_questions} distinct Multiple-Choice Questions (MCQs) at {difficulty} difficulty.

STRICT QUALITY RULES:
1. Write specific, meaningful questions that test real concepts, definitions, chapters, practicals, rules, or metrics from the text.
2. NEVER ask generic questions like "Which statement is directly supported by the document analysis?".
3. Provide 1 correct answer and 3 plausible wrong answers (distractors) that belong to the SAME subject area and tone as the document.
4. Keep all 4 options similar in length and grammatical style. Do NOT copy-paste broken sentence fragments.
5. Include a 1-sentence "explanation" stating why the correct answer is right according to that page.

Document Excerpts:
{document_context}

Return ONLY a valid JSON array of {num_questions} objects in this exact schema (no markdown text outside the JSON):
[
  {{
    "question": "Specific question testing a concept from the document?",
    "correct_answer": "The exact correct option text",
    "wrong_answers": [
      "Plausible wrong option 1 from the same subject",
      "Plausible wrong option 2 from the same subject",
      "Plausible wrong option 3 from the same subject"
    ],
    "page": 1,
    "explanation": "Brief explanation citing the fact from the page."
  }}
]"""

    try:
        raw_response = await llm_client.generate_text(prompt, temperature=0.3)
        match = re.search(r"\[.*\]", raw_response, flags=re.DOTALL)
        if match:
            raw_questions = json.loads(match.group(0))
            if isinstance(raw_questions, list) and len(raw_questions) > 0:
                formatted_quiz = []
                option_labels = ["A", "B", "C", "D"]

                for idx, q in enumerate(raw_questions[:num_questions], start=1):
                    correct_text = str(q.get("correct_answer", "")).strip()
                    wrong_answers = q.get("wrong_answers", [])
                    distractors = [str(w).strip() for w in wrong_answers[:3]]

                    while len(distractors) < 3:
                        distractors.append(f"Alternative theoretical scenario {len(distractors) + 1}")

                    all_options = [correct_text] + distractors
                    random.shuffle(all_options)

                    correct_index = all_options.index(correct_text)
                    correct_letter = option_labels[correct_index]

                    formatted_quiz.append({
                        "id": idx,
                        "question": str(q.get("question", "")).strip(),
                        "page": int(q.get("page", 1)),
                        "options": {
                            "A": all_options[0],
                            "B": all_options[1],
                            "C": all_options[2],
                            "D": all_options[3],
                        },
                        "correct_option": correct_letter,
                        "correct_index": correct_index,
                        "explanation": str(q.get("explanation", ""))
                    })

                if len(formatted_quiz) >= num_questions:
                    return formatted_quiz
    except Exception:
        pass

    return generate_local_conceptual_quiz(
        doc_name=doc_name,
        all_doc_chunks=all_doc_chunks,
        num_questions=num_questions,
        difficulty=difficulty
    )


class QuizEngineService:

    @classmethod
    async def generate_quiz_questions(
        cls,
        document_id: int,
        number_of_questions: int,
        difficulty: str,
        database_session: AsyncSession
    ) -> List[QuizQuestionRecord]:
        document_query = select(DocumentRecord).where(DocumentRecord.id == document_id)
        document_query_result = await database_session.execute(document_query)
        target_document = document_query_result.scalars().first()

        if not target_document:
            raise ValueError(f"Document with ID {document_id} was not found.")

        chunks_query = (
            select(DocumentChunkRecord)
            .where(DocumentChunkRecord.document_id == document_id)
            .order_by(DocumentChunkRecord.chunk_index_number)
        )
        chunks_query_result = await database_session.execute(chunks_query)
        retrieved_chunks = chunks_query_result.scalars().all()

        if not retrieved_chunks:
            raise ValueError(f"Document with ID {document_id} has no indexed text chunks.")

        # Purge old questions for this document to ensure fresh generation
        await database_session.execute(
            delete(QuizQuestionRecord).where(QuizQuestionRecord.document_id == document_id)
        )
        await database_session.flush()

        all_doc_chunks = [
            {
                "page": chunk.source_page_number or 1,
                "text": chunk.chunk_text_content,
                "id": chunk.id
            }
            for chunk in retrieved_chunks
        ]

        raw_questions_data = await generate_quiz_questions_llm(
            doc_name=target_document.filename,
            all_doc_chunks=all_doc_chunks,
            num_questions=number_of_questions,
            difficulty=difficulty,
            llm_client=LLMClient
        )

        created_question_records = []
        for question_dict in raw_questions_data:
            new_question_record = QuizQuestionRecord(
                document_id=document_id,
                question_text=question_dict["question"],
                option_a=question_dict["options"]["A"],
                option_b=question_dict["options"]["B"],
                option_c=question_dict["options"]["C"],
                option_d=question_dict["options"]["D"],
                correct_option=question_dict["correct_option"].upper(),
                explanation=question_dict.get("explanation"),
                source_page_number=int(question_dict.get("page", 1)),
                difficulty=difficulty
            )
            database_session.add(new_question_record)
            created_question_records.append(new_question_record)

        await database_session.commit()
        for record in created_question_records:
            await database_session.refresh(record)

        return created_question_records

    @classmethod
    async def get_document_questions(
        cls,
        document_id: int,
        database_session: AsyncSession
    ) -> List[QuizQuestionRecord]:
        query = (
            select(QuizQuestionRecord)
            .where(QuizQuestionRecord.document_id == document_id)
            .order_by(QuizQuestionRecord.id)
        )
        result = await database_session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def submit_quiz_attempt(
        cls,
        user_id: int,
        document_id: int,
        submitted_answers: List[Dict[str, Any]],
        database_session: AsyncSession
    ) -> Dict[str, Any]:
        question_ids = [item["question_id"] for item in submitted_answers]
        questions_query = select(QuizQuestionRecord).where(QuizQuestionRecord.id.in_(question_ids))
        questions_result = await database_session.execute(questions_query)
        questions_map = {q.id: q for q in questions_result.scalars().all()}

        total_questions = len(submitted_answers)
        correct_count = 0
        answer_result_items = []

        for sub_ans in submitted_answers:
            qid = sub_ans["question_id"]
            selected_opt = sub_ans["selected_option"].strip().upper()
            target_question = questions_map.get(qid)

            if target_question:
                is_correct = (selected_opt == target_question.correct_option.upper())
                if is_correct:
                    correct_count += 1

                answer_result_items.append({
                    "question_id": qid,
                    "question_text": target_question.question_text,
                    "selected_option": selected_opt,
                    "correct_option": target_question.correct_option,
                    "is_correct": is_correct,
                    "explanation": target_question.explanation,
                    "source_page_number": target_question.source_page_number
                })

        score_percentage = round((correct_count / total_questions) * 100.0, 2) if total_questions > 0 else 0.0

        new_attempt = QuizAttemptRecord(
            user_id=user_id,
            document_id=document_id,
            total_questions=total_questions,
            correct_count=correct_count,
            score_percentage=score_percentage
        )
        database_session.add(new_attempt)
        await database_session.flush()

        for ans_item in answer_result_items:
            new_ans_record = QuizAnswerRecord(
                attempt_id=new_attempt.id,
                question_id=ans_item["question_id"],
                selected_option=ans_item["selected_option"],
                is_correct=ans_item["is_correct"]
            )
            database_session.add(new_ans_record)

        await database_session.commit()
        await database_session.refresh(new_attempt)

        return {
            "attempt_id": new_attempt.id,
            "document_id": document_id,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "score_percentage": score_percentage,
            "answers": answer_result_items,
            "completed_at": new_attempt.completed_at
        }

    @classmethod
    async def get_quiz_history(
        cls,
        user_id: int,
        document_id: int,
        database_session: AsyncSession
    ) -> Dict[str, Any]:
        history_query = (
            select(QuizAttemptRecord)
            .where(QuizAttemptRecord.user_id == user_id, QuizAttemptRecord.document_id == document_id)
            .order_by(desc(QuizAttemptRecord.completed_at))
        )
        history_result = await database_session.execute(history_query)
        attempts = list(history_result.scalars().all())

        if not attempts:
            return {
                "document_id": document_id,
                "attempts": [],
                "best_score_percentage": 0.0,
                "average_score_percentage": 0.0
            }

        scores = [att.score_percentage for att in attempts]
        return {
            "document_id": document_id,
            "attempts": attempts,
            "best_score_percentage": max(scores),
            "average_score_percentage": round(sum(scores) / len(scores), 2)
        }

    @classmethod
    async def get_spaced_repetition_review(
        cls,
        user_id: int,
        document_id: int,
        database_session: AsyncSession
    ) -> List[QuizQuestionRecord]:
        incorrect_answers_query = (
            select(QuizAnswerRecord.question_id)
            .join(QuizAttemptRecord, QuizAnswerRecord.attempt_id == QuizAttemptRecord.id)
            .where(
                QuizAttemptRecord.user_id == user_id,
                QuizAttemptRecord.document_id == document_id,
                QuizAnswerRecord.is_correct == False
            )
            .distinct()
        )
        incorrect_result = await database_session.execute(incorrect_answers_query)
        failed_question_ids = list(incorrect_result.scalars().all())

        if not failed_question_ids:
            latest_questions = await cls.get_document_questions(document_id, database_session)
            return latest_questions[:5]

        review_query = select(QuizQuestionRecord).where(QuizQuestionRecord.id.in_(failed_question_ids))
        review_result = await database_session.execute(review_query)
        return list(review_result.scalars().all())
