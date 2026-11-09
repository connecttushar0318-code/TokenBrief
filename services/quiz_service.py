import json
import re
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from models import (
    QuizQuestionRecord,
    QuizAttemptRecord,
    QuizAnswerRecord,
    DocumentRecord,
    DocumentChunkRecord
)
from config import settings

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

        raw_questions_data = None
        if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
            raw_questions_data = await cls._try_gemini_quiz_generation(
                target_document=target_document,
                chunks=retrieved_chunks,
                number_of_questions=number_of_questions,
                difficulty=difficulty
            )

        if not raw_questions_data:
            raw_questions_data = cls._generate_fallback_quiz_questions(
                target_document=target_document,
                chunks=retrieved_chunks,
                number_of_questions=number_of_questions,
                difficulty=difficulty
            )

        created_question_records = []
        for question_dict in raw_questions_data:
            new_question_record = QuizQuestionRecord(
                document_id=document_id,
                question_text=question_dict["question_text"],
                option_a=question_dict["option_a"],
                option_b=question_dict["option_b"],
                option_c=question_dict["option_c"],
                option_d=question_dict["option_d"],
                correct_option=question_dict["correct_option"].upper(),
                explanation=question_dict.get("explanation"),
                source_page_number=question_dict.get("source_page_number", 1),
                difficulty=difficulty
            )
            database_session.add(new_question_record)
            created_question_records.append(new_question_record)

        await database_session.commit()
        for record in created_question_records:
            await database_session.refresh(record)

        return created_question_records

    @classmethod
    async def _try_gemini_quiz_generation(
        cls,
        target_document: DocumentRecord,
        chunks: List[DocumentChunkRecord],
        number_of_questions: int,
        difficulty: str
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            from google import genai
            from google.genai import types

            sampled_chunks = chunks[:15]
            aggregated_context = "\n\n".join(
                [f"[Page {chunk.source_page_number}] {chunk.chunk_text_content}" for chunk in sampled_chunks]
            )

            client = genai.Client(api_key=settings.gemini_api_key)
            prompt = (
                f"You are a test preparation expert. Generate {number_of_questions} multiple-choice questions "
                f"at {difficulty} difficulty based strictly on this document titled '{target_document.filename}'.\n"
                f"Context:\n{aggregated_context[:14000]}\n\n"
                f"Output strictly valid JSON as an array of objects with keys: "
                f"'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option' (must be 'A', 'B', 'C', or 'D'), "
                f"'explanation', 'source_page_number' (integer).\n"
                f"Do not include markdown code fence formatting."
            )

            response = client.models.generate_content(
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
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed[:number_of_questions]
            if isinstance(parsed, dict) and "questions" in parsed:
                return parsed["questions"][:number_of_questions]
        except Exception:
            return None
        return None

    @classmethod
    def _generate_fallback_quiz_questions(
        cls,
        target_document: DocumentRecord,
        chunks: List[DocumentChunkRecord],
        number_of_questions: int,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        is_resume = "resume" in target_document.filename.lower() or "cv" in target_document.filename.lower()
        aggregated_text = "\n".join([chunk.chunk_text_content for chunk in chunks])
        cleaned_text = re.sub(r"\[Document:.*?\]", "", aggregated_text)

        candidate_questions = []

        if is_resume:
            candidate_questions.extend(cls._extract_resume_quiz_items(cleaned_text, chunks))
        else:
            candidate_questions.extend(cls._extract_document_concept_quiz_items(cleaned_text, chunks))

        if len(candidate_questions) < number_of_questions:
            candidate_questions.extend(cls._extract_general_fact_quiz_items(cleaned_text, chunks))

        while len(candidate_questions) < number_of_questions:
            page_num = chunks[0].source_page_number or 1
            candidate_questions.append({
                "question_text": f"What is the principal subject covered in '{target_document.filename}'?",
                "option_a": f"The core domain methodologies and detailed content of {target_document.filename.replace('.pdf', '')}",
                "option_b": "General accounting and tax guidelines",
                "option_c": "Unrelated peripheral hardware specifications",
                "option_d": "Fictional storytelling and scriptwriting",
                "correct_option": "A",
                "explanation": f"The primary subject matter focuses directly on the domain information documented within {target_document.filename}.",
                "source_page_number": page_num
            })

        return candidate_questions[:number_of_questions]

    @classmethod
    def _extract_resume_quiz_items(cls, text: str, chunks: List[DocumentChunkRecord]) -> List[Dict[str, Any]]:
        questions = []
        page_num = chunks[0].source_page_number or 1

        name_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", text.strip())
        if name_match:
            person_name = name_match.group(1).strip()
            questions.append({
                "question_text": f"Who is the candidate profiled in this document?",
                "option_a": person_name,
                "option_b": "Dr. Sarah Jenkins",
                "option_c": "Michael R. Thompson",
                "option_d": "Alex Morgan",
                "correct_option": "A",
                "explanation": f"The header of the resume identifies {person_name} as the candidate.",
                "source_page_number": page_num
            })

        skills_match = re.search(r"(?:Technical Skills|Skills|Technologies|Competencies)[:\s]+([^\n\r]+)", text, re.IGNORECASE)
        if skills_match:
            skills_string = skills_match.group(1)
            skill_items = [s.strip() for s in re.split(r"[,|•\-\n]", skills_string) if len(s.strip()) > 2]
            if len(skill_items) >= 2:
                correct_skill = skill_items[0]
                questions.append({
                    "question_text": f"Which technical skill or technology is explicitly listed in the candidate's profile?",
                    "option_a": "Objective-C & COBOL Legacy Systems",
                    "option_b": correct_skill,
                    "option_c": "Assembly x86 Microcode",
                    "option_d": "Fortran 77 Numerical Analysis",
                    "correct_option": "B",
                    "explanation": f"The candidate's technical skills section directly lists '{correct_skill}'.",
                    "source_page_number": page_num
                })

        education_match = re.search(r"(?:B\.?Tech|Bachelor|Master|Degree|B\.?E\.?|B\.?S\.?|University|College|Institute)[^\n\r]+", text, re.IGNORECASE)
        if education_match:
            edu_text = education_match.group(0).strip()[:80]
            questions.append({
                "question_text": "Which educational background or institution is documented in the profile?",
                "option_a": "Harvard Medical School Postdoctoral Fellowship",
                "option_b": "London School of Economics Maritime Law",
                "option_c": edu_text,
                "option_d": "Tokyo University Architecture Department",
                "correct_option": "C",
                "explanation": f"The education section indicates: '{edu_text}'.",
                "source_page_number": page_num
            })

        projects_match = re.findall(r"(?:Project|Title|Work)[:\s]+([^\n\r]+)", text, re.IGNORECASE)
        if projects_match:
            project_name = projects_match[0].strip()[:70]
            questions.append({
                "question_text": "What project or initiative did the candidate develop or contribute to?",
                "option_a": project_name,
                "option_b": "Submarine Sonar Waveform Calibrator",
                "option_c": "High-Frequency Automated Wall Street Trader",
                "option_d": "Aerospace Combustion Modeling Framework",
                "correct_option": "A",
                "explanation": f"The candidate's portfolio includes the project '{project_name}'.",
                "source_page_number": page_num
            })

        return questions

    @classmethod
    def _extract_document_concept_quiz_items(cls, text: str, chunks: List[DocumentChunkRecord]) -> List[Dict[str, Any]]:
        questions = []
        definition_pattern = re.compile(
            r"([A-Z][a-zA-Z0-9\s\-]{2,35})\s+(?:is defined as|refers to|is the process of|consists of|is a technique for)\s+([^\.\n]+)\.",
            re.IGNORECASE
        )

        matches = definition_pattern.findall(text)
        for term, definition_body in matches[:8]:
            cleaned_term = term.strip()
            cleaned_def = definition_body.strip()
            if len(cleaned_term) > 3 and len(cleaned_def) > 15:
                matching_page = 1
                for chk in chunks:
                    if cleaned_term.lower() in chk.chunk_text_content.lower():
                        matching_page = chk.source_page_number or 1
                        break

                shuffled_options = [
                    (cleaned_def[:100], "correct"),
                    ("The physical extraction of rare earth minerals from rock formations", "distractor1"),
                    ("A hardware protocol governing motherboard bus voltages", "distractor2"),
                    ("A legal standard determining intellectual property licensing in Europe", "distractor3")
                ]
                random.shuffle(shuffled_options)
                correct_letter = "A"
                for idx, (opt_text, opt_role) in enumerate(shuffled_options):
                    if opt_role == "correct":
                        correct_letter = ["A", "B", "C", "D"][idx]

                questions.append({
                    "question_text": f"According to the text, what is {cleaned_term}?",
                    "option_a": shuffled_options[0][0],
                    "option_b": shuffled_options[1][0],
                    "option_c": shuffled_options[2][0],
                    "option_d": shuffled_options[3][0],
                    "correct_option": correct_letter,
                    "explanation": f"The document defines {cleaned_term} as: {cleaned_def}.",
                    "source_page_number": matching_page
                })

        return questions

    @classmethod
    def _extract_general_fact_quiz_items(cls, text: str, chunks: List[DocumentChunkRecord]) -> List[Dict[str, Any]]:
        questions = []
        bullet_points = re.findall(r"(?:•|\*|-|\d+\.)\s+([A-Z][^\.\n]{20,120}\.)", text)

        for bp in bullet_points[:5]:
            sentence = bp.strip()
            words = sentence.split()
            if len(words) >= 6:
                source_page = 1
                for chk in chunks:
                    if words[0] in chk.chunk_text_content:
                        source_page = chk.source_page_number or 1
                        break

                questions.append({
                    "question_text": f"Which statement is directly supported by the document analysis?",
                    "option_a": sentence,
                    "option_b": "All operations must strictly execute on mainframe hardware without networks.",
                    "option_c": "The system completely disables automated processing and indexing.",
                    "option_d": "Standard manual paperwork is mandated for every transaction.",
                    "correct_option": "A",
                    "explanation": f"Document context confirms: '{sentence}'.",
                    "source_page_number": source_page
                })

        return questions

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
