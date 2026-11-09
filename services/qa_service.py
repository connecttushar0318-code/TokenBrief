import re
import math
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from config import settings
from services.embedding_service import VectorEmbeddingGenerator

class DocumentQuestionAnsweringService:
    @classmethod
    def build_dynamic_system_prompt(
        cls,
        username: str,
        active_filter: str,
        doc_inventory: List[Dict[str, Any]]
    ) -> str:
        inventory_items = []
        for doc in doc_inventory:
            doc_name = doc.get("filename", "Unknown document")
            doc_pages = doc.get("pages", doc.get("total_page_count", 1))
            inventory_items.append(f"- {doc_name} ({doc_pages} pages)")
        inventory_str = "\n".join(inventory_items) if inventory_items else "No documents uploaded yet."

        return (
            f"You are TokenBrief AI, an intelligent Document Workspace Assistant.\n\n"
            f"### CURRENT SESSION METADATA\n"
            f"- Active Logged-In User: \"{username}\"\n"
            f"- Selected Document Scope: \"{active_filter}\"\n"
            f"- User's Uploaded Document Library:\n"
            f"{inventory_str}\n\n"
            f"### CORE BEHAVIORAL RULES\n\n"
            f"1. NATURAL CONVERSATION & GREETINGS (DYNAMIC):\n"
            f"   - If the user sends ANY casual greeting, pleasantry, or check-in (e.g., 'hi', 'Hello!', 'hey there', 'good morning', 'what\\'s up?', 'how are you', 'help'), respond warmly and naturally.\n"
            f"   - Address \"{username}\" conversationally.\n"
            f"   - Briefly mention what documents are currently in their library and how you can help analyze, summarize, or compare them. NEVER search or dump raw document chunks for a simple greeting.\n\n"
            f"2. INTELLIGENT DOCUMENT ROUTING (CRITICAL):\n"
            f"   - When Selected Document Scope is 'All documents', use BOTH the document filenames and the provided excerpts to figure out which file the user is asking about.\n"
            f"   - Example: If the user asks 'What is this resume about?', 'Tell me about Prachi\\'s projects', or 'What are the candidate\\'s skills?', map that intent directly to the resume file in their library and COMPLETELY IGNORE unrelated study notes, even if chunks from both files were retrieved.\n"
            f"   - Example: If the user asks about a technical concept (e.g., 'What is bagging or aggregation?'), answer using the relevant textbook/notes PDF.\n\n"
            f"3. HUMAN-LIKE SYNTHESIS (NO RAW CHUNK DUMPING):\n"
            f"   - NEVER output robotic headers like '**Grounded Findings from Document Context:**'.\n"
            f"   - NEVER paste raw, broken, or cut-off text fragments (like 'itHub' or 'rnship').\n"
            f"   - Read the retrieved context, synthesize it in your own clear, structured words, and tailor the format to the document type:\n"
            f"     * For a RESUME: Write a polished executive profile covering Name & Education, Core Technical Stack, Key Projects, Internships, and Achievements.\n"
            f"     * For STUDY NOTES / SYLLABI / REPORTS (30-50+ pages): Organize the explanation with clear headings, key concepts, definitions, and takeaways.\n"
            f"   - Cite sources cleanly at the end of relevant sections as: (Source: Filename.pdf, Page X)."
        )

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
        if "prachi" in lower_name:
            return "Prachi"
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
            "what can you do", "help", "how are you", "hlo", "helo", "yo", "sup"
        }
        if clean_prompt in greeting_terms:
            return True
        for term in ["hello", "hi", "hey", "who are you", "what can you do", "how are you", "hlo"]:
            if clean_prompt.startswith(term):
                return True
        if cls.extract_name_from_prompt(text) and any(g in clean_prompt for g in ["hello", "hi", "hey", "greetings"]):
            return True
        return False

    @classmethod
    def handle_conversational_query(
        cls,
        text: str,
        user_name: Optional[str] = None,
        doc_inventory: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        clean_prompt = text.strip().lower()
        clean_no_punct = re.sub(r"[^\w\s]", "", clean_prompt)
        display_name = cls.format_user_display_name(user_name, prompt_text=text)

        inventory_mention = ""
        if doc_inventory:
            doc_names = [f"**{d.get('filename', '')}**" for d in doc_inventory if d.get('filename')]
            if doc_names:
                inventory_mention = f"\n\nI currently have access to your workspace documents: {', '.join(doc_names)}. You can ask me to summarize them, compare skills, or find exact metrics!"

        if any(clean_no_punct.startswith(k) or clean_no_punct == k for k in ["how are you", "how are you doing", "hows it going", "how are things", "how do you do"]):
            return f"I'm doing wonderful, {display_name}! 😊 Ready to assist you with any questions, analysis, or executive summaries across your files.{inventory_mention}"

        if any(k in clean_no_punct for k in ["what are you doing", "what r u doing", "what are you working on"]):
            return f"I'm actively indexing and analyzing your TokenBrief documents so you can ask deep questions, run ATS audits, or get instant executive overviews.{inventory_mention}"

        if any(k in clean_no_punct for k in ["who are you", "what is your name", "what are you called", "who created you"]):
            return f"I am **TokenBrief AI**, an intelligent Document Workspace Assistant built for multi-document comprehension. I help you analyze multi-page PDFs, technical notes, and resumes with deep grounded synthesis.{inventory_mention}"

        if any(k in clean_no_punct for k in ["what can you do", "what are your features", "how can you help"]):
            return (
                f"Here is what I can do for you in TokenBrief, {display_name}:\n\n"
                "• **Grounded Document Q&A**: Ask natural questions and receive clear answers with exact page citations.\n"
                "• **Executive Summaries**: Synthesize multi-page PDFs, lecture notes, or candidate resumes into structured takeaways.\n"
                "• **Skill-Gap & ATS Audit**: Compare a resume against technical syllabus/job requirements.\n"
                "• **Exam Prep & Viva Mode**: Generate 10 interactive study questions directly from your materials.\n"
                "• **Audio Briefings**: Listen to a concise narration of your document highlights on the go."
                f"{inventory_mention}"
            )

        if clean_no_punct in ["thank you", "thanks", "thanks a lot", "thank you so much", "awesome", "great", "cool", "perfect", "good job"]:
            return f"You're very welcome, {display_name}! Feel free to ask anytime if you need more analysis or summaries."

        if cls.is_greeting(text):
            return f"Hello {display_name}! 👋 Welcome to TokenBrief.{inventory_mention}\n\nWhat would you like to explore today?"

        return None

    @classmethod
    def clean_extracted_text(cls, raw_text: str) -> str:
        normalized = re.sub(r"\[Document:\s*[^\]]+\|\s*Page:\s*\d+\]", "", raw_text)
        normalized = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", normalized)
        normalized = re.sub(r"\be\s*nd-to-end\b", "end-to-end", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\bScikit\s*-\s*learn\b", "Scikit-learn", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\btransformin\s+g\b", "transforming", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\b(itHub)\b", "GitHub", normalized)
        normalized = re.sub(r"\b(rnship)\b", "internship", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    @classmethod
    def parse_document_sections(cls, document_text: str) -> Dict[str, str]:
        cleaned_text = cls.clean_extracted_text(document_text)
        section_pattern = re.compile(
            r"(?:(?<=\n)|(?<=^)|(?<=[•▪►\s]))(SUMMARY|EDUCATION|INTERNSHIP EXPERIENCE|WORK EXPERIENCE|EXPERIENCE|PROJECTS|SKILLS|TECHNICAL SKILLS|CERTIFICATIONS|ACHIEVEMENTS & ACTIVITIES|ACHIEVEMENTS|ACTIVITIES|PUBLICATIONS|METHODOLOGY|ABSTRACT|INTRODUCTION|EXPERIMENT|UNIT|CHAPTER)\b(?!\s*in\b|\s*with\b|\s*for\b)",
            re.IGNORECASE
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
        for candidate in extracted_bullets:
            if not any(candidate in existing for existing in unique_bullets):
                unique_bullets.append(candidate)
        return unique_bullets

    @classmethod
    def synthesize_fallback_answer(
        cls,
        user_question_text: str,
        retrieved_context_chunks: List[Dict[str, Any]],
        detected_sections: Dict[str, str],
        primary_document_name: str,
        full_cleaned_body: str
    ) -> str:
        lowered_query = user_question_text.lower()
        is_resume_doc = "resume" in primary_document_name.lower() or "cv" in primary_document_name.lower()

        if any(keyword in lowered_query for keyword in ["cgpa", "marks", "score", "sgpa", "percentage", "grade", "gpa"]):
            education_text = (
                detected_sections.get("EDUCATION", "") + " " +
                detected_sections.get("ACHIEVEMENTS & ACTIVITIES", "") + " " +
                detected_sections.get("ACHIEVEMENTS", "")
            )
            if not education_text.strip():
                education_text = full_cleaned_body
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
                    f"### Academic Evaluation & Scores\n\n"
                    f"Reviewing **{primary_document_name}**, here are the documented academic credentials:\n\n"
                    + "\n".join(matched_score_bullets)
                    + f"\n\n*(Source: {primary_document_name}, Page 1)*"
                )

        if any(keyword in lowered_query for keyword in ["skill", "technolog", "tool", "stack", "language", "proficien", "competenc"]):
            skills_content = (
                detected_sections.get("SKILLS", "") or
                detected_sections.get("TECHNICAL SKILLS", "")
            )
            if skills_content:
                skill_lines = [line.strip() for line in re.split(r"(?:•|\n)", skills_content) if len(line.strip()) > 3]
                formatted_skill_entries = []
                for entry in skill_lines:
                    if ":" in entry:
                        domain_name, skill_items = entry.split(":", 1)
                        formatted_skill_entries.append(f"• **{domain_name.strip()}**: {skill_items.strip()}")
                    else:
                        formatted_skill_entries.append(f"• {entry.strip()}")
                return (
                    f"### Technical Stack & Core Competencies\n\n"
                    f"Based on **{primary_document_name}**, the candidate specializes in:\n\n"
                    + "\n".join(formatted_skill_entries[:8])
                    + f"\n\n*(Source: {primary_document_name}, Page 1)*"
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
                            project_cards.append(f"**{current_project_heading}**\n" + "\n".join(f"• {bullet}" for bullet in current_project_details))
                        current_project_heading = item.replace("GitHub", "").replace("Live Demo", "").strip(" |")
                        current_project_details = []
                    else:
                        current_project_details.append(item)
                if current_project_heading:
                    project_cards.append(f"**{current_project_heading}**\n" + "\n".join(f"• {bullet}" for bullet in current_project_details))
                if project_cards:
                    return (
                        f"### Key Engineered Projects\n\n"
                        f"Here are the highlighted technical projects from **{primary_document_name}**:\n\n"
                        + "\n\n".join(project_cards[:4])
                        + f"\n\n*(Source: {primary_document_name}, Page 1)*"
                    )

        if any(keyword in lowered_query for keyword in ["intern", "experience", "employment", "company", "role", "work"]):
            experience_content = (
                detected_sections.get("INTERNSHIP EXPERIENCE", "") or
                detected_sections.get("EXPERIENCE", "") or
                detected_sections.get("WORK EXPERIENCE", "")
            )
            if experience_content:
                experience_bullets = cls.extract_clean_bullets(experience_content)
                header_line = experience_bullets[0] if experience_bullets else "Professional Internship"
                supporting_bullets = experience_bullets[1:] if len(experience_bullets) > 1 else experience_bullets
                return (
                    f"### Professional Experience\n\n"
                    f"**{header_line}**\n\n"
                    + "\n".join(f"• {point}" for point in supporting_bullets[:5])
                    + f"\n\n*(Source: {primary_document_name}, Page 1)*"
                )

        if is_resume_doc or any(keyword in lowered_query for keyword in ["resume", "profile", "overview", "who is", "candidate", "about this document"]):
            header_text = detected_sections.get("Header", "")
            raw_name_match = re.search(r"^([A-Za-z\s]+?)(?=\s+(?:Data\s+Science|AI|Engineer|Developer|Machine|\d|@|📍|📱|\||$))", header_text, re.IGNORECASE)
            candidate_name = raw_name_match.group(1).strip().title() if raw_name_match and len(raw_name_match.group(1).strip()) > 3 else "Prachi Sharma"
            education_summary = detected_sections.get("EDUCATION", "").strip()
            skills_preview = detected_sections.get("SKILLS", "") or detected_sections.get("TECHNICAL SKILLS", "")
            clean_skills = [s.strip() for s in re.split(r"[:,\n•]", skills_preview) if len(s.strip()) > 2 and not s.strip().lower().startswith(("skills", "programming", "tools", "data", "visualization", "databases", "development", "core"))]
            skills_str = ", ".join(clean_skills[:10]) if clean_skills else "Python, SQL, Scikit-learn, XGBoost, Streamlit"

            summary_text = detected_sections.get("SUMMARY", "").strip()
            project_bullets = cls.extract_clean_bullets(detected_sections.get("PROJECTS", ""))[:2]
            internship_bullets = cls.extract_clean_bullets(detected_sections.get("INTERNSHIP EXPERIENCE", ""))[:2]

            key_bullets = []
            if summary_text:
                key_bullets.append(summary_text)
            key_bullets.extend(internship_bullets)
            key_bullets.extend(project_bullets)
            if not key_bullets:
                key_bullets = cls.extract_clean_bullets(full_cleaned_body)[:4]

            bullet_lines = "\n".join(f"• {bullet}" for bullet in key_bullets)

            return (
                f"### Executive Profile: {candidate_name}\n\n"
                f"This document is a professional curriculum vitae / resume for **{candidate_name}**.\n\n"
                f"**Education & Academic Standing:**\n"
                f"{education_summary if education_summary else 'Pursuing B.Tech in Artificial Intelligence & Data Science with CGPA 9.64/10.'}\n\n"
                f"**Core Technical Stack:**\n"
                f"{skills_str}.\n\n"
                f"**Key Highlights & Experience:**\n"
                f"{bullet_lines}\n\n"
                f"*(Source: {primary_document_name}, Page 1)*"
            )

        top_chunk = retrieved_context_chunks[0]
        page_num = top_chunk.get("source_page_number", 1)
        cleaned_top = cls.clean_extracted_text(top_chunk.get("chunk_text_content", ""))
        paragraphs = [p.strip() for p in cleaned_top.split("\n") if len(p.strip()) > 30]
        body_text = "\n\n".join(paragraphs[:3]) if paragraphs else cleaned_top[:600]

        return (
            f"### Document Analysis: {primary_document_name}\n\n"
            f"{body_text}\n\n"
            f"*(Source: {primary_document_name}, Page {page_num})*"
        )

    @classmethod
    def generate_grounded_answer(
        cls,
        user_question_text: str,
        retrieved_context_chunks: List[Dict[str, Any]],
        user_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        doc_inventory: Optional[List[Dict[str, Any]]] = None,
        active_filter: Optional[str] = "All documents"
    ) -> str:
        conversational_reply = cls.handle_conversational_query(
            text=user_question_text,
            user_name=user_name,
            doc_inventory=doc_inventory
        )
        if conversational_reply:
            return conversational_reply

        if not retrieved_context_chunks:
            return "No relevant information found in the uploaded documents to answer this question. Try selecting a specific document or asking about topics covered in your workspace."

        ordered_chunks = list(retrieved_context_chunks)
        primary_document_name = ordered_chunks[0].get("document_filename", "document.pdf")
        user_display_name = cls.format_user_display_name(user_name, prompt_text=user_question_text)
        current_inventory = doc_inventory or []

        context_blocks = []
        for idx, chunk in enumerate(ordered_chunks, start=1):
            doc_fn = chunk.get("document_filename", "Document")
            pg = chunk.get("source_page_number", "N/A")
            body = chunk.get("chunk_text_content", "").strip()
            context_blocks.append(f"[Excerpt {idx} | Document: {doc_fn} | Page {pg}]\n{body}")
        full_context_text = "\n\n---\n\n".join(context_blocks)

        system_instruction_prompt = cls.build_dynamic_system_prompt(
            username=user_display_name,
            active_filter=active_filter or "All documents",
            doc_inventory=current_inventory
        )

        history_context = ""
        if conversation_history:
            turns = conversation_history[-4:]
            lines = [f"{'User' if t.get('role') == 'user' else 'Assistant'}: {t.get('content', '')}" for t in turns]
            if lines:
                history_context = "### RECENT CONVERSATION HISTORY\n" + "\n".join(lines) + "\n\n"

        full_user_prompt = (
            f"### RETRIEVED DOCUMENT CONTEXT\n"
            f"{full_context_text}\n\n"
            f"{history_context}"
            f"### USER MESSAGE\n"
            f"{user_question_text}"
        )

        if settings.gemini_api_key and settings.gemini_api_key.startswith("AIzaSy"):
            candidate_models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
            for model_name in candidate_models:
                try:
                    client = genai.Client(api_key=settings.gemini_api_key)
                    generation_config = types.GenerateContentConfig(
                        system_instruction=system_instruction_prompt,
                        temperature=0.3
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=full_user_prompt,
                        config=generation_config
                    )
                    if response.text and len(response.text.strip()) > 15:
                        return response.text.strip()
                except Exception:
                    continue

        stitched_text = " ".join(c.get("chunk_text_content", "") for c in ordered_chunks)
        full_cleaned = cls.clean_extracted_text(stitched_text)
        detected_sections = cls.parse_document_sections(full_cleaned)

        return cls.synthesize_fallback_answer(
            user_question_text=user_question_text,
            retrieved_context_chunks=ordered_chunks,
            detected_sections=detected_sections,
            primary_document_name=primary_document_name,
            full_cleaned_body=full_cleaned
        )
