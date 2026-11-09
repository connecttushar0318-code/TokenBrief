import re
import math
from typing import List, Dict, Any, Optional
from google import genai
from config import settings
from services.embedding_service import VectorEmbeddingGenerator

class DocumentQuestionAnsweringService:
    @classmethod
    @classmethod
    def extract_name_from_prompt(cls, prompt_text: str) -> Optional[str]:
        matched_name = re.search(r"\b(?:my name is|i am|this is|call me|myself)\s+([A-Za-z]+)", prompt_text, re.IGNORECASE)
        if matched_name:
            candidate = matched_name.group(1).strip()
            if candidate.lower() not in {"here", "there", "a", "an", "the", "user", "asking", "just", "now", "fine", "good"}:
                return candidate.capitalize()
        return None

    @classmethod
    def format_user_display_name(cls, raw_username: Optional[str], prompt_text: Optional[str] = None) -> str:
        if prompt_text:
            prompt_name = cls.extract_name_from_prompt(prompt_text)
            if prompt_name:
                return prompt_name
        if not raw_username:
            return "there"
        clean_text = raw_username.strip()
        lower_name = clean_text.lower()
        if "rohit" in lower_name:
            return "Rohit"
        if "tushar" in lower_name:
            return "Tushar"
        if "_" in clean_text:
            parts = [part.capitalize() for part in clean_text.split("_") if part]
            return " ".join(parts) if parts else clean_text.capitalize()
        return clean_text.capitalize()

    @classmethod
    def is_greeting(cls, text: str) -> bool:
        clean_prompt = text.strip().lower()
        clean_prompt = re.sub(r"[^\w\s]", "", clean_prompt)
        greeting_terms = {
            "hi", "hello", "hey", "hola", "greetings", "good morning",
            "good afternoon", "good evening", "namaste", "who are you",
            "what can you do", "help", "how are you"
        }
        if clean_prompt in greeting_terms:
            return True
        for term in ["hello", "hi", "hey", "who are you", "what can you do"]:
            if clean_prompt.startswith(term):
                return True
        if cls.extract_name_from_prompt(text) and any(g in clean_prompt for g in ["hello", "hi", "hey", "greetings"]):
            return True
        return False

    @classmethod
    def clean_extracted_text(cls, raw_text: str) -> str:
        normalized_text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", raw_text)
        normalized_text = re.sub(r"\be\s*nd-to-end\b", "end-to-end", normalized_text, flags=re.IGNORECASE)
        normalized_text = re.sub(r"\bScikit\s*-\s*learn\b", "Scikit-learn", normalized_text, flags=re.IGNORECASE)
        normalized_text = re.sub(r"\btransformin\s+g\b", "transforming", normalized_text, flags=re.IGNORECASE)
        normalized_text = re.sub(r"(?<=\.\s)(?=[A-Z][A-Za-z\s]{3,40}\|)", "\n\n", normalized_text)
        normalized_text = re.sub(r"[ \t]+", " ", normalized_text)
        return normalized_text.strip()

    @classmethod
    def stitch_overlapping_chunks(cls, chunk_texts: List[str]) -> str:
        if not chunk_texts:
            return ""
        stitched_content = chunk_texts[0]
        for incoming_chunk in chunk_texts[1:]:
            overlap_detected = False
            maximum_window = min(len(stitched_content), len(incoming_chunk), 250)
            for window_size in range(maximum_window, 8, -1):
                if stitched_content.endswith(incoming_chunk[:window_size]):
                    stitched_content += incoming_chunk[window_size:]
                    overlap_detected = True
                    break
            if not overlap_detected:
                stitched_content += "\n\n" + incoming_chunk
        return stitched_content

    @classmethod
    def parse_document_sections(cls, document_text: str) -> Dict[str, str]:
        cleaned_text = cls.clean_extracted_text(document_text)
        section_pattern = re.compile(
            r"(?:(?<=\n)|(?<=^)|(?<=[•▪►\s]))(SUMMARY|EDUCATION|INTERNSHIP EXPERIENCE|WORK EXPERIENCE|EXPERIENCE|PROJECTS|SKILLS|TECHNICAL SKILLS|CERTIFICATIONS|ACHIEVEMENTS & ACTIVITIES|ACHIEVEMENTS|ACTIVITIES|PUBLICATIONS|METHODOLOGY|ABSTRACT|INTRODUCTION|RESULTS|CONCLUSION)\b(?!\s*in\b|\s*with\b|\s*for\b)",
        )
        found_matches = list(section_pattern.finditer(cleaned_text))
        structured_sections = {}
        if not found_matches:
            structured_sections["Overview"] = cleaned_text
            return structured_sections

        if found_matches[0].start() > 0:
            pre_header = cleaned_text[:found_matches[0].start()].strip()
            if pre_header:
                structured_sections["Header"] = pre_header

        for index in range(len(found_matches)):
            section_name = found_matches[index].group(0).strip().upper()
            start_index = found_matches[index].end()
            end_index = found_matches[index + 1].start() if index + 1 < len(found_matches) else len(cleaned_text)
            body_content = cleaned_text[start_index:end_index].strip(" :-\t\r\n")
            if body_content:
                structured_sections[section_name] = body_content

        return structured_sections

    @classmethod
    def extract_clean_bullets(cls, section_text: str) -> List[str]:
        raw_elements = re.split(r"(?:[•▪►]|\n\n|\n)", section_text)
        extracted_bullets = []
        for element in raw_elements:
            cleaned_bullet = element.strip(" •▪►-\t\r\n")
            if len(cleaned_bullet) >= 10:
                extracted_bullets.append(cleaned_bullet)
        unique_bullets = []
        sorted_by_length = sorted(extracted_bullets, key=len, reverse=True)
        for candidate in sorted_by_length:
            if not any(candidate in existing for existing in unique_bullets):
                unique_bullets.append(candidate)
        return [item for item in extracted_bullets if item in unique_bullets]

    @classmethod
    def compute_cosine_similarity(cls, vector_a: List[float], vector_b: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        magnitude_a = math.sqrt(sum(a * a for a in vector_a))
        magnitude_b = math.sqrt(sum(b * b for b in vector_b))
        if magnitude_a == 0.0 or magnitude_b == 0.0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)

    @classmethod
    def handle_greeting_response(
        cls,
        user_name: str,
        retrieved_context_chunks: List[Dict[str, Any]],
        detected_sections: Dict[str, str],
        prompt_text: Optional[str] = None
    ) -> str:
        display_name = cls.format_user_display_name(user_name, prompt_text=prompt_text)
        if not retrieved_context_chunks:
            return (
                f"Hello {display_name}! 👋 Welcome to TokenBrief.\n\n"
                "Your document workspace is currently ready. Upload any document on the right to start exploring with deep conversational intelligence and structured summaries."
            )

        doc_filename = retrieved_context_chunks[0]["document_filename"]
        suggested_bullet_topics = []

        if "EDUCATION" in detected_sections or "ACHIEVEMENTS" in detected_sections or "ACHIEVEMENTS & ACTIVITIES" in detected_sections:
            suggested_bullet_topics.append("• **Academic Qualifications & Scores**: CGPA, degree, and coursework details")
        if "SKILLS" in detected_sections or "TECHNICAL SKILLS" in detected_sections:
            suggested_bullet_topics.append("• **Technical Stack & Skills**: Languages, frameworks, machine learning, and databases")
        if "PROJECTS" in detected_sections:
            suggested_bullet_topics.append("• **Projects & Portfolio**: Architecture, datasets, algorithms, and deployed solutions")
        if "INTERNSHIP EXPERIENCE" in detected_sections or "EXPERIENCE" in detected_sections:
            suggested_bullet_topics.append("• **Experience & Industry Exposure**: Roles, contributions, and key metrics")
        if "CERTIFICATIONS" in detected_sections:
            suggested_bullet_topics.append("• **Certifications**: Professional credentials and courses")

        if not suggested_bullet_topics:
            suggested_bullet_topics = [
                "• Key concepts, definitions, and highlights",
                "• Important statistics, scores, and dates",
                "• Structured breakdowns and project details",
                "• Executive summaries and takeaways"
            ]

        topics_formatted = "\n".join(suggested_bullet_topics)
        return (
            f"Hello {display_name}! 👋 Welcome to TokenBrief.\n\n"
            f"I have thoroughly analyzed and indexed your workspace document: **{doc_filename}**.\n\n"
            f"Here are key areas you can ask me about:\n"
            f"{topics_formatted}\n\n"
            "What would you like to explore?"
        )

    @classmethod
    def generate_grounded_answer(
        cls,
        user_question_text: str,
        retrieved_context_chunks: List[Dict[str, Any]],
        user_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        if not retrieved_context_chunks:
            return "No relevant information found in the uploaded documents to answer this question. Try selecting 'All documents' or asking about topics covered in your uploaded files."

        ordered_context_chunks = sorted(
            retrieved_context_chunks,
            key=lambda item: (item.get("document_id", 0), item.get("chunk_index_number", item.get("chunk_id", 0)))
        )
        first_chunk = ordered_context_chunks[0]
        primary_document_name = first_chunk["document_filename"]
        chunk_text_collection = [chunk["chunk_text_content"] for chunk in ordered_context_chunks]
        full_stitched_text = cls.stitch_overlapping_chunks(chunk_text_collection)
        cleaned_document_body = cls.clean_extracted_text(full_stitched_text)
        detected_sections = cls.parse_document_sections(cleaned_document_body)

        if cls.is_greeting(user_question_text):
            return cls.handle_greeting_response(
                user_name=user_name or "there",
                retrieved_context_chunks=ordered_context_chunks,
                detected_sections=detected_sections,
                prompt_text=user_question_text
            )

        formatted_context_sections = []
        source_counter = 1
        for single_chunk in retrieved_context_chunks:
            source_citation = (
                f"Source {source_counter} "
                f"(Document: {single_chunk['document_filename']}, "
                f"Page: {single_chunk.get('source_page_number', 'N/A')}):"
            )
            formatted_context_sections.append(
                f"{source_citation}\n{single_chunk['chunk_text_content']}"
            )
            source_counter += 1

        combined_context_text = "\n\n".join(formatted_context_sections)

        history_context = ""
        if conversation_history:
            recent_turns = conversation_history[-4:]
            formatted_history = []
            for turn in recent_turns:
                speaker = "User" if turn.get("role") == "user" else "Assistant"
                formatted_history.append(f"{speaker}: {turn.get('content', '')}")
            if formatted_history:
                history_context = "Conversation History:\n" + "\n".join(formatted_history) + "\n\n"

        generation_prompt = (
            "You are TokenBrief AI, an advanced document intelligence assistant powered by Generative AI.\n"
            "Answer the question thoroughly, accurately, and cleanly using the provided document context below.\n"
            "Format your answer with clear markdown headings, bullet points, and highlight key terms where appropriate.\n"
            "Cite the source document and page number in your response when referencing specific facts.\n"
            "If the information is not contained in the context, explicitly say what is known and what is missing.\n\n"
            f"{history_context}"
            f"Context:\n{combined_context_text}\n\n"
            f"Question: {user_question_text}\n\n"
            "Answer:"
        )

        if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
            candidate_models = [settings.gemini_model_name, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
            for model_name in candidate_models:
                try:
                    gemini_api_client = genai.Client(api_key=settings.gemini_api_key)
                    response = gemini_api_client.models.generate_content(
                        model=model_name,
                        contents=generation_prompt
                    )
                    if response.text and len(response.text.strip()) > 15:
                        return response.text.strip()
                except Exception:
                    continue

        lowered_query = user_question_text.lower()

        if any(keyword in lowered_query for keyword in ["cgpa", "marks", "score", "sgpa", "percentage", "grade", "gpa"]):
            education_text = (
                detected_sections.get("EDUCATION", "") + " " +
                detected_sections.get("ACHIEVEMENTS & ACTIVITIES", "") + " " +
                detected_sections.get("ACHIEVEMENTS", "")
            )
            if not education_text.strip():
                education_text = cleaned_document_body
            sentence_splits = re.split(r"(?:•|\n|(?<=[a-z0-9])\.\s+(?=[A-Z]))", education_text)
            matched_score_bullets = []
            for sentence in sentence_splits:
                cleaned_sentence = sentence.strip(" •-\t\r\n")
                if len(cleaned_sentence) > 10 and any(kw in cleaned_sentence.lower() for kw in ["cgpa", "sgpa", "score", "grade", "marks", "b.tech", "semester"]):
                    if cleaned_sentence not in matched_score_bullets:
                        if any(highlight_word in cleaned_sentence.lower() for highlight_word in ["cgpa", "sgpa", "9.64", "10.0"]):
                            matched_score_bullets.append(f"• **{cleaned_sentence}**")
                        else:
                            matched_score_bullets.append(f"• {cleaned_sentence}")
            if matched_score_bullets:
                return (
                    f"**Academic Metrics & Evaluation Scores (from {primary_document_name}):**\n\n"
                    + "\n".join(matched_score_bullets)
                    + f"\n\n*(Source: {primary_document_name})*"
                )

        if any(keyword in lowered_query for keyword in ["skill", "technolog", "tool", "stack", "language", "proficien", "competenc"]):
            skills_content = detected_sections.get("SKILLS", "") or detected_sections.get("TECHNICAL SKILLS", "")
            if skills_content:
                skill_lines = [line.strip() for line in skills_content.split("\n") if line.strip()]
                formatted_skill_entries = []
                for entry in skill_lines:
                    if ":" in entry:
                        domain_name, skill_items = entry.split(":", 1)
                        formatted_skill_entries.append(f"• **{domain_name.strip()}**: {skill_items.strip()}")
                    else:
                        formatted_skill_entries.append(f"• {entry.strip()}")
                return (
                    f"**Technical Skills & Core Competencies (from {primary_document_name}):**\n\n"
                    + "\n".join(formatted_skill_entries)
                    + f"\n\n*(Source: {primary_document_name})*"
                )

        if any(keyword in lowered_query for keyword in ["project", "portfolio", "built", "model", "system"]):
            projects_content = detected_sections.get("PROJECTS", "")
            if projects_content:
                project_bullets = cls.extract_clean_bullets(projects_content)
                project_cards = []
                current_project_heading = ""
                current_project_details = []
                action_verbs = ("created", "engineered", "evaluated", "deployed", "designed", "connected", "delivered", "examined", "leveraged", "crafted", "built")
                for item in project_bullets:
                    if any(contact_sym in item.lower() for contact_sym in ["@", "📍", "📱", "linkedin", "github.com", "phone", "email"]):
                        continue
                    is_title_candidate = (
                        "|" in item or
                        (len(item) < 85 and not item.lower().startswith(action_verbs))
                    )
                    if is_title_candidate:
                        if current_project_heading:
                            project_cards.append(f"### {current_project_heading}\n" + "\n".join(f"• {bullet}" for bullet in current_project_details))
                        current_project_heading = item.replace("GitHub", "").replace("Live Demo", "").strip(" |")
                        current_project_details = []
                    else:
                        current_project_details.append(item)
                if current_project_heading:
                    project_cards.append(f"### {current_project_heading}\n" + "\n".join(f"• {bullet}" for bullet in current_project_details))
                if project_cards:
                    return (
                        f"**Featured Projects (from {primary_document_name}):**\n\n"
                        + "\n\n".join(project_cards)
                        + f"\n\n*(Source: {primary_document_name})*"
                    )

        if any(keyword in lowered_query for keyword in ["intern", "experience", "employment", "company", "role", "work"]):
            experience_content = (
                detected_sections.get("INTERNSHIP EXPERIENCE", "") or
                detected_sections.get("EXPERIENCE", "") or
                detected_sections.get("WORK EXPERIENCE", "")
            )
            if experience_content:
                experience_bullets = cls.extract_clean_bullets(experience_content)
                header_line = experience_bullets[0] if experience_bullets else "Professional Experience"
                supporting_bullets = experience_bullets[1:] if len(experience_bullets) > 1 else experience_bullets
                return (
                    f"**Professional Experience (from {primary_document_name}):**\n\n"
                    f"### {header_line}\n"
                    + "\n".join(f"• {point}" for point in supporting_bullets)
                    + f"\n\n*(Source: {primary_document_name})*"
                )

        if any(keyword in lowered_query for keyword in ["who is", "profile", "overview", "background", "summary", "candidate"]):
            summary_section_text = detected_sections.get("SUMMARY", "") or detected_sections.get("Overview", "")
            overall_bullets = cls.extract_clean_bullets(cleaned_document_body)[:4]
            return (
                f"**Profile Overview & Background (from {primary_document_name}):**\n\n"
                f"{summary_section_text}\n\n"
                f"**Key Highlights:**\n"
                + "\n".join(f"• {bullet}" for bullet in overall_bullets)
                + f"\n\n*(Source: {primary_document_name})*"
            )

        query_embedding_vector = VectorEmbeddingGenerator.generate_single_embedding(user_question_text)
        semantic_candidate_units = []
        for single_chunk in retrieved_context_chunks:
            chunk_body = single_chunk["chunk_text_content"]
            split_units = [u.strip() for u in re.split(r"(?:[•▪►]|\n\n|\n|(?<=[.!?])\s+(?=[A-Z0-9]))", chunk_body) if len(u.strip()) > 15]
            for unit_text in split_units:
                semantic_candidate_units.append({
                    "text": unit_text,
                    "document_filename": single_chunk["document_filename"],
                    "source_page_number": single_chunk.get("source_page_number", 1)
                })

        if semantic_candidate_units:
            unit_texts_list = [item["text"] for item in semantic_candidate_units]
            unit_embeddings_list = VectorEmbeddingGenerator.generate_batch_embeddings(unit_texts_list)
            query_word_set = set(re.findall(r"\w+", lowered_query))

            for unit_index in range(len(semantic_candidate_units)):
                dense_sim = cls.compute_cosine_similarity(query_embedding_vector, unit_embeddings_list[unit_index])
                unit_word_set = set(re.findall(r"\w+", semantic_candidate_units[unit_index]["text"].lower()))
                sparse_overlap = len(query_word_set.intersection(unit_word_set)) / max(len(query_word_set), 1)
                hybrid_score = (0.65 * dense_sim) + (0.35 * sparse_overlap)
                semantic_candidate_units[unit_index]["hybrid_score"] = hybrid_score

            semantic_candidate_units.sort(key=lambda item: item["hybrid_score"], reverse=True)

            selected_findings = []
            registered_texts = set()
            top_document_name = semantic_candidate_units[0]["document_filename"]
            top_page_number = semantic_candidate_units[0]["source_page_number"]

            for item in semantic_candidate_units[:5]:
                clean_item_text = item["text"].strip(" •-\t\r\n")
                if clean_item_text not in registered_texts and item["hybrid_score"] > 0.18:
                    registered_texts.add(clean_item_text)
                    selected_findings.append(f"• {clean_item_text}")

            if selected_findings:
                combined_findings = "\n".join(selected_findings)
                return (
                    f"**Grounded Findings from Document Context:**\n\n"
                    f"{combined_findings}\n\n"
                    f"*(Source: {top_document_name}, Page {top_page_number})*"
                )

        return f"{first_chunk['chunk_text_content'][:450]}... *(Source: {first_chunk['document_filename']}, Page {first_chunk.get('source_page_number', 1)})*"
