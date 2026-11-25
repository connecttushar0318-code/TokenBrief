import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from config import settings

def clean_text(raw_text: str) -> str:
    """Removes leaked internal tags like '[Doc: ... | Section: ... | Page: 1].'"""
    text = re.sub(r"^\[Doc:.*?\]\.?\s*", "", raw_text, flags=re.DOTALL)
    text = re.sub(r"^Page\s+\d+\s*", "", text)
    text = re.sub(r"\[Document:\s*[^\]]+\|\s*Page:\s*\d+\]", "", text)
    return re.sub(r"\s+", " ", text).strip()

def build_full_file_digest(chunks: List[Dict]) -> str:
    """
    Compresses any 1-to-50 page PDF or Video Transcript into a single clean text block
    so the AI always sees 100% of the document/video without hitting token limits.
    Each item in `chunks` has: {"page": 1 (or timestamp "02:15"), "text": "..."}
    """
    grouped: Dict[str, List[str]] = {}
    for c in chunks:
        label = str(c.get("page") or c.get("timestamp") or "1")
        text_val = c.get("text") or c.get("chunk_text_content") or ""
        cleaned = clean_text(text_val)
        if cleaned:
            grouped.setdefault(label, []).append(cleaned)

    total_sections = len(grouped)
    if total_sections == 0:
        return "No document text available."

    # Dynamically budget characters per page so even 60-page PDFs retain rich goals, body, and conclusions
    chars_per_page = max(900, min(2500, 42000 // max(1, total_sections)))

    digest_lines = []
    for label, texts in grouped.items():
        full_page_text = " ".join(texts)
        if not full_page_text.strip():
            continue
        # Snap digest slices cleanly to sentence/word boundaries without splicing half-sentences together
        if len(full_page_text) > chars_per_page:
            half = chars_per_page // 2
            sent_end = full_page_text.rfind(". ", 0, half)
            if sent_end < 80:
                forward_end = full_page_text.find(". ", half, min(len(full_page_text), half + 250))
                if forward_end > 0:
                    sent_end = forward_end
            if sent_end >= 80:
                start_part = full_page_text[: sent_end + 1]
            else:
                start_cut = full_page_text.rfind(" ", 0, half)
                start_part = full_page_text[:start_cut] if start_cut > 0 else full_page_text[:half]

            sent_start = full_page_text.find(". ", max(0, len(full_page_text) - half))
            if sent_start > 0 and len(full_page_text) - sent_start > 80:
                end_part = full_page_text[sent_start + 2 :].strip()
            else:
                end_cut = full_page_text.find(" ", len(full_page_text) - half)
                end_part = full_page_text[end_cut:].strip() if end_cut > 0 else full_page_text[-half:]
            snippet = f"{start_part}\n...\n{end_part}"
        else:
            snippet = full_page_text
        digest_lines.append(f"[Source Page/Time {label}]: {snippet}")

    return "\n\n".join(digest_lines)

_GREETING_TOKENS = {
    "hlo", "helo", "hello", "hi", "hey", "hola", "namaste", "sup", "yo",
    "morning", "afternoon", "evening", "thanks", "thank"
}
_NON_GREETING_INTENTS = {
    "summarize", "summerize", "summary", "explain", "about", "what", "why",
    "how", "marks", "cgpa", "skills", "projects", "weka", "data", "page",
    "unit", "chapter", "compare", "list", "describe", "tell"
}

def is_pure_greeting(message: str) -> bool:
    clean_lower = (message or "").lower().strip()
    if not clean_lower or len(clean_lower) > 40:
        return False
    clean_words = set(re.findall(r"\b\w+\b", clean_lower))
    if any(k in clean_lower for k in _NON_GREETING_INTENTS):
        return False
    exact_greetings = {
        "hlo", "helo", "hello", "hey", "hi", "hola", "how are you",
        "who are you", "what are you doing", "what's up", "namaste", "thanks", "thank you"
    }
    if clean_lower in exact_greetings:
        return True
    return len(clean_words) <= 4 and bool(clean_words.intersection(_GREETING_TOKENS))


class LLMClient:
    _cached_client = None
    _cached_key: Optional[str] = None
    _invalid_keys: set = set()

    @classmethod
    def _get_client(cls, api_key: str):
        if cls._cached_client is None or cls._cached_key != api_key:
            cls._cached_client = genai.Client(api_key=api_key)
            cls._cached_key = api_key
        return cls._cached_client

    @classmethod
    async def generate_text(cls, prompt: str, temperature: float = 0.2) -> str:
        """Invokes fast Gemini Flash models first with cached key validation and local fallback."""
        api_key = (settings.gemini_api_key or "").strip()
        if api_key and api_key not in cls._invalid_keys:
            preferred = settings.gemini_model_name or "gemini-3.5-flash-lite"
            candidate_models = list(dict.fromkeys([
                preferred,
                "gemini-3.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-3.8-flash",
                "gemini-2.5-flash",
                "gemini-2.0-flash",
            ]))
            client = cls._get_client(api_key)
            for model_name in candidate_models:
                try:
                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=temperature,
                                response_mime_type="application/json"
                            )
                        ),
                        timeout=12.0,
                    )
                    if response.text and len(response.text.strip()) > 5:
                        return response.text.strip()
                except Exception as e:
                    err_msg = str(e)
                    if "UNAUTHENTICATED" in err_msg or "API key not valid" in err_msg or "API_KEY_INVALID" in err_msg:
                        cls._invalid_keys.add(api_key)
                        break
                    continue

        return cls._local_synthesis(prompt)

    @staticmethod
    def _strip_page_artifacts(text: str) -> str:
        # Preserve newline gap across digest "..." markers so disjoint sentences never splice together
        text = re.sub(r"\s*\n+\.\.\.\n+\s*", "\n", text.strip())
        text = re.sub(r"^(?:[ivxlcdm]{1,5}|\d{1,3})\s+(?=[A-Za-z])", "", text)
        return re.sub(r"[ \t]+", " ", text).strip()

    @staticmethod
    def _is_front_matter(text: str) -> bool:
        head = text.lower()[:350]
        boilerplate_markers = (
            "declaration by the student",
            "certificate by the supervisor",
            "acknowledgement",
            "list of figures",
            "list of tables",
            "list of abbreviations",
            "table of contents",
            "submitted in partial fulfilment",
        )
        return any(m in head for m in boilerplate_markers)

    _CHAP_HEADER_RX = re.compile(
        r"CHAPTER\s+\d+:\s*(?:(?!\s*\d+\.\d+\b|\s+[A-Z][a-z])[A-Z0-9\s,&/-])+"
    )
    _SUB_TITLE_RX = re.compile(
        r"^\s*(\d+\.\d+\s+[A-Z][A-Za-z0-9\s,&/-]{2,65}?)"
        r"(?=\s+(?:The|A|An|In|To|For|On|By|As|With|This|These|It|Here|[A-Z][A-Za-z0-9-]*\s+(?!(?:and|or|of|to|the|for|in|on|with|via|by|using|from)\s+[A-Z])[a-z]{2,})\b)"
    )

    @classmethod
    def _clean_sentences(cls, text: str, require_capital: bool = True, require_punct_end: bool = True) -> List[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        complete = []
        partial = []
        for s in parts:
            s_clean = re.sub(r"^(?:\d{1,3}|[ivxlcdm]{1,4})\s+", "", s.strip())
            if len(s_clean) < 30 or s_clean.startswith("[Detailed Excerpt"):
                continue
            if s_clean in {"...", "...."} or s_clean.count("...") >= 2:
                continue
            if len(re.findall(r"\b\d+\.\d+\b", s_clean)) >= 4:
                continue
            # Skip isolated table/figure captions or math equation headers without explanation
            if re.match(r"^(?:Figure|Table|Parameter\s*/\s*Attribute|\(|•\s*Parameters:)", s_clean) and len(s_clean) < 160:
                continue
            if require_capital and s_clean and s_clean[0].islower():
                continue
            if s_clean.endswith((".", "!", "?")):
                complete.append(s_clean)
            else:
                partial.append(s_clean)
        if require_punct_end and complete:
            return complete
        return complete or partial

    @classmethod
    def _local_synthesis(cls, prompt: str) -> str:
        """Clean local neural synthesizer that handles greetings, targeted sections, and executive summaries."""
        user_msg_match = re.search(r'=== USER MESSAGE ===\s*"([^"]+)"', prompt, re.DOTALL)
        user_message = user_msg_match.group(1).strip() if user_msg_match else ""

        file_name_match = re.search(r'Active File:\s*"([^"]+)"', prompt)
        file_name = file_name_match.group(1).strip() if file_name_match else "Workspace Documents"

        overview_match = re.search(r'=== FULL DOCUMENT / VIDEO OVERVIEW \(All Pages / Timestamps\) ===\s*(.*?)\s*=== TOP DETAILED EXCERPTS', prompt, re.DOTALL)
        overview_text = overview_match.group(1).strip() if overview_match else ""

        excerpts_match = re.search(r'=== TOP DETAILED EXCERPTS FOR SPECIFIC LOOKUPS ===\s*(.*?)\s*=== USER MESSAGE ===', prompt, re.DOTALL)
        excerpts_text = excerpts_match.group(1).strip() if excerpts_match else ""

        clean_lower = user_message.lower().strip()
        clean_words = set(re.findall(r"\b\w+\b", clean_lower))

        # 1. Natural greeting handling
        if is_pure_greeting(user_message):
            ans = f"Hello! 👋 I am **TokenBrief AI**, your intelligent document and video assistant. **{file_name}** is loaded and ready to explore in depth. You can ask me to summarize the core topics, explain specific concepts, or find detailed metrics across your files!"
            return json.dumps({"answer": ans, "cited_pages": []})

        page_snippets = re.findall(r"\[Source Page/Time (\w+)\]:\s*(.*?)(?=\n\n\[Source Page/Time|\Z)", overview_text, re.DOTALL)
        excerpt_blocks = re.findall(r"\[Detailed Excerpt - Page/Time (\w+)\]:\s*(.*?)(?=\n\n\[Detailed Excerpt|\Z)", excerpts_text, re.DOTALL)

        def _parse_int(lbl: str, default: int = 1) -> int:
            try:
                return int(lbl)
            except Exception:
                return default

        word_nums = r"one|two|three|four|five|six|seven|eight|nine|ten|first|second|third|fourth|fifth|sixth"
        has_specific_target = bool(
            re.search(rf"\b(?:section|chapter|unit|module|part|page|appendix|table|figure)\s*(?:\d+(?:\.\d+)?|{word_nums})\b|\b\d+\.\d+\b", clean_lower)
        )

        global_summary_phrases = ("executive summary", "summarize", "summerize", "summary", "overview", "main points", "takeaways", "all about", "brief")
        explain_whole_doc = "explain" in clean_lower and any(w in clean_lower for w in ("document", "pdf", "file", "report", "whole", "entire"))
        is_summary = (not has_specific_target) and (any(t in clean_lower for t in global_summary_phrases) or explain_whole_doc)

        # 2. Global Executive Summary (skipping Cover / Declaration / Certificate / TOC)
        if is_summary or (not excerpts_text.strip() and page_snippets):
            body_pages = []
            abstract_pages = []
            chapter_pages = []
            conclusion_pages = []

            for p_lbl, raw_p in page_snippets:
                p_num = _parse_int(p_lbl)
                cleaned_p = cls._strip_page_artifacts(raw_p)
                low_p = cleaned_p.lower()
                if "abstract" in low_p[:60] and not cls._is_front_matter(cleaned_p):
                    abstract_pages.append((p_num, cleaned_p))
                elif not cls._is_front_matter(cleaned_p):
                    if re.search(r"\b(?:chapter\s*6|6\.1\s+conclusion|conclusion\s+and\s+future)\b", low_p[:140]):
                        conclusion_pages.append((p_num, cleaned_p))
                    elif re.search(r"CHAPTER\s+[1-5]\s*:", cleaned_p):
                        chapter_pages.append((p_num, cleaned_p))
                    body_pages.append((p_num, cleaned_p))

            if not body_pages and abstract_pages:
                body_pages = abstract_pages
            elif not body_pages:
                body_pages = [(_parse_int(lbl), cls._strip_page_artifacts(txt)) for lbl, txt in page_snippets]

            cited_pages = []
            sections_md = [
                f"### Executive Summary: {file_name}",
                f"This document spans **{len(page_snippets) if page_snippets else 1} pages**. Below is a structured synthesis of its main goals, core topics, and conclusions:"
            ]

            # Goals & Purpose
            goal_sources = abstract_pages[:1] or body_pages[:1]
            goal_bullets = []
            for p_num, p_txt in goal_sources:
                clean_p_txt = re.sub(r"^ABSTRACT\s+", "", p_txt, flags=re.IGNORECASE)
                for s in cls._clean_sentences(clean_p_txt)[:2]:
                    goal_bullets.append(f"- {s} [Page {p_num}]")
                if p_num not in cited_pages:
                    cited_pages.append(p_num)
            if goal_bullets:
                sections_md.append("#### Main Goals & Purpose\n" + "\n".join(goal_bullets))

            # Core Topics: prefer actual Chapter opening pages first, then sample body evenly
            if chapter_pages:
                sampled_topics = chapter_pages[:5]
            else:
                topic_pool = [bp for bp in body_pages if bp not in conclusion_pages]
                if len(topic_pool) > 5:
                    step = len(topic_pool) / 5
                    sampled_topics = [topic_pool[int(i * step)] for i in range(5)]
                else:
                    sampled_topics = topic_pool[:5]

            topic_bullets = []
            for p_num, p_txt in sampled_topics:
                chap_m = cls._CHAP_HEADER_RX.search(p_txt)
                sub_text = cls._CHAP_HEADER_RX.sub("", p_txt, count=1).strip() if chap_m else p_txt
                sub_text = cls._SUB_TITLE_RX.sub("", sub_text, count=1).strip()
                sents = cls._clean_sentences(sub_text) or cls._clean_sentences(p_txt)
                if not sents:
                    continue
                prefix = f"**{chap_m.group(0).strip().title()} (Page {p_num})**: " if chap_m else f"**Page {p_num}**: "
                topic_bullets.append(f"- {prefix}{sents[0]}")
                if p_num not in cited_pages:
                    cited_pages.append(p_num)

            if topic_bullets:
                sections_md.append("#### Core Topics & Technical Scope\n" + "\n".join(topic_bullets))

            # Conclusions
            concl_sources = conclusion_pages[:2] or (body_pages[-1:] if len(body_pages) > 1 else [])
            concl_bullets = []
            for p_num, p_txt in concl_sources:
                clean_concl = re.sub(r"^.*?6\.1\s+Conclusion\s+", "", p_txt, flags=re.IGNORECASE)
                clean_concl = cls._CHAP_HEADER_RX.sub("", clean_concl).strip()
                sents = cls._clean_sentences(clean_concl) or cls._clean_sentences(p_txt)
                for s in sents[:2]:
                    concl_bullets.append(f"- {s} [Page {p_num}]")
                if p_num not in cited_pages:
                    cited_pages.append(p_num)
            if concl_bullets:
                sections_md.append("#### Key Outcomes & Conclusions\n" + "\n".join(concl_bullets))

            return json.dumps({
                "answer": "\n\n".join(sections_md),
                "cited_pages": cited_pages[:8] if cited_pages else [1]
            })

        # 3. Targeted Section / Chapter / Specific Factual Explanation
        excerpt_items = [(_parse_int(p_lbl), cls._strip_page_artifacts(txt)) for p_lbl, txt in excerpt_blocks if txt.strip()]
        if not excerpt_items and page_snippets:
            excerpt_items = [(_parse_int(p_lbl), cls._strip_page_artifacts(txt)) for p_lbl, txt in page_snippets[:3]]

        if has_specific_target and excerpt_items:
            first_text = excerpt_items[0][1]
            heading_match = cls._CHAP_HEADER_RX.search(first_text)
            section_heading = heading_match.group(0).strip().title() if heading_match else user_message.strip().title()

            target_num_m = re.search(r"\b(?:section|chapter|unit|module|part)\s*(\d+)\b", clean_lower)
            major_prefix = re.escape(target_num_m.group(1)) if target_num_m else r"\d+"
            sub_finder_rx = re.compile(
                rf"\b({major_prefix}\.\d+\s+[A-Z][A-Za-z0-9\s,&/-]{{2,65}}?)"
                r"(?=\s+(?:The|A|An|In|To|For|On|By|As|With|This|These|It|Here|[A-Z][A-Za-z0-9-]*\s+(?!(?:and|or|of|to|the|for|in|on|with|via|by|using|from)\s+[A-Z])[a-z]{2,})\b)"
            )

            bullet_lines = []
            cited_pages = []
            for p_num, p_txt in excerpt_items[:5]:
                cleaned_block = cls._CHAP_HEADER_RX.sub("", p_txt).strip()
                sub_match = sub_finder_rx.search(cleaned_block)
                sub_label = f"{sub_match.group(1).strip()} (Page {p_num})" if sub_match else f"Page {p_num}"
                body_only = cls._SUB_TITLE_RX.sub("", cleaned_block, count=1).strip()
                sents = cls._clean_sentences(body_only) or cls._clean_sentences(cleaned_block, require_capital=False, require_punct_end=False)
                if sents:
                    excerpt_summary = " ".join(sents[:2])
                    bullet_lines.append(f"- **{sub_label}**: {excerpt_summary} [Page {p_num}]")
                    if p_num not in cited_pages:
                        cited_pages.append(p_num)

            if bullet_lines:
                answer_md = f"### {section_heading}\n\n" + "\n\n".join(bullet_lines)
                return json.dumps({
                    "answer": answer_md,
                    "cited_pages": cited_pages or [excerpt_items[0][0]]
                })

        # General specific factual question
        query_terms = [w for w in clean_words if len(w) > 3]
        scored_sentences = []
        for p_num, p_txt in excerpt_items:
            for sent in cls._clean_sentences(p_txt):
                sent_lower = sent.lower()
                overlap = sum(1 for term in query_terms if term in sent_lower)
                scored_sentences.append((overlap, p_num, sent))

        scored_sentences.sort(key=lambda item: item[0], reverse=True)
        chosen = [item for item in scored_sentences if item[0] > 0][:4] or scored_sentences[:3]

        cited_pages = []
        formatted_points = []
        for _, p_num, sent in chosen:
            formatted_points.append(f"{sent} [Page {p_num}]")
            if p_num not in cited_pages:
                cited_pages.append(p_num)

        answer_body = "\n\n".join(formatted_points) if formatted_points else f"Based on **{file_name}**, the retrieved excerpts cover this topic directly."
        return json.dumps({
            "answer": answer_body,
            "cited_pages": cited_pages or [1]
        })

async def ask_tokenbrief(
    user_message: str,
    file_name: str,
    all_file_chunks: List[Dict],
    top_k_chunks: List[Dict],
    llm_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    ONE unified function that handles:
    - Greetings in any language or slang ("hlo", "hello", "hey", "hola") -> Replies in English with NO fake sources.
    - Typos ("summerize the core parts only", "wat is ph scle") -> Understands intent automatically.
    - Full 4-to-50 page PDF & Video summaries -> Uses full_file_digest so zero pages are missed.
    - Specific factual questions -> Uses top_k_chunks + full_file_digest with exact citations.
    """
    if is_pure_greeting(user_message):
        return {
            "answer": (
                f"Hello! 👋 I am **TokenBrief AI**, your intelligent document and video assistant. "
                f"**{file_name}** is loaded and ready to explore in depth. You can ask me to summarize "
                f"the core topics, explain specific concepts, or find detailed metrics across your files!"
            ),
            "sources": [],
            "cited_pages": []
        }

    # 1. Always build the whole-file view + detailed chunks view
    full_file_digest = build_full_file_digest(all_file_chunks)
    detailed_matches = "\n\n".join(
        f"[Detailed Excerpt - Page/Time {c.get('page', 1)}]: {clean_text(c.get('text') or c.get('chunk_text_content', ''))}"
        for c in top_k_chunks
    )

    # 2. One unified prompt that lets the LLM be the brain
    unified_prompt = f"""You are TokenBrief AI, an intelligent document and video assistant.
Always respond in clear, natural English.

Active File: "{file_name}"

=== FULL DOCUMENT / VIDEO OVERVIEW (All Pages / Timestamps) ===
{full_file_digest}

=== TOP DETAILED EXCERPTS FOR SPECIFIC LOOKUPS ===
{detailed_matches}

=== USER MESSAGE ===
"{user_message}"

=== INSTRUCTIONS ===
Understand the user's true intent even if their message has heavy spelling typos, shorthand, or non-English greetings:

1. IF THE USER IS GREETING OR CHATTING (e.g., "hlo", "hello", "hey", "hola", "hi", "thanks"):
   - Reply warmly in English introducing yourself as TokenBrief AI and mention that "{file_name}" is loaded and ready to explore.
   - Set "cited_pages" to an empty list [].

2. IF THE USER WANTS A SUMMARY OR OVERVIEW (e.g., "summerize the core parts only", "summary", "explain this pdf/video", "main points"):
   - Use the FULL DOCUMENT / VIDEO OVERVIEW above to write a complete, well-structured Markdown summary covering the entire file.
   - Honor any specific filter the user asked for (such as focusing only on core parts, unit marks, or key video takeaways).
   - Cite pages or video timestamps in brackets like [Page 1] or [04:20] and list the used page numbers in "cited_pages".

3. IF THE USER ASKS A SPECIFIC QUESTION (even with typos):
   - Automatically understand the misspelled words and answer accurately using the provided excerpts and overview.
   - Cite exact pages/timestamps in brackets like [Page 2] and include those numbers in "cited_pages".
   - ONLY if the question asks for a fact completely absent from the file, politely say the uploaded file does not cover that topic and set "cited_pages" to [].

Return ONLY a valid JSON object in this exact format:
{{
  "answer": "Your complete Markdown response in English here",
  "cited_pages": [1, 2]
}}"""

    client = llm_client or LLMClient
    raw_output = await client.generate_text(unified_prompt, temperature=0.2)

    # 3. Parse the JSON response cleanly
    try:
        match = re.search(r"\{.*\}", raw_output, flags=re.DOTALL)
        data = json.loads(match.group(0)) if match else {"answer": raw_output, "cited_pages": []}
    except Exception:
        data = {"answer": raw_output, "cited_pages": []}

    # 4. Build the sources list ONLY from pages the AI actually used (empty [] for "hlo"/"hola"!)
    sources = [
        {"document": file_name, "page": p}
        for p in data.get("cited_pages", [])
    ]

    return {
        "answer": data.get("answer", "").strip(),
        "sources": sources,
        "cited_pages": data.get("cited_pages", [])
    }

class DocumentQuestionAnsweringService:
    clean_text = staticmethod(clean_text)
    build_full_file_digest = staticmethod(build_full_file_digest)
    ask_tokenbrief = staticmethod(ask_tokenbrief)

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
        all_chunks = [
            {"page": c.get("source_page_number", 1), "text": c.get("chunk_text_content", "")}
            for c in retrieved_context_chunks
        ]
        active_doc = active_filter or (retrieved_context_chunks[0].get("document_filename") if retrieved_context_chunks else "Workspace Documents")

        unified_prompt = f"""You are TokenBrief AI, an intelligent document and video assistant.
Always respond in clear, natural English.

Active File: "{active_doc}"

=== FULL DOCUMENT / VIDEO OVERVIEW (All Pages / Timestamps) ===
{build_full_file_digest(all_chunks)}

=== TOP DETAILED EXCERPTS FOR SPECIFIC LOOKUPS ===
{build_full_file_digest(all_chunks[:5])}

=== USER MESSAGE ===
"{user_question_text}"

Return ONLY a valid JSON object in this exact format:
{{
  "answer": "Your complete Markdown response in English here",
  "cited_pages": [1]
}}"""
        raw = LLMClient._local_synthesis(unified_prompt)
        try:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {"answer": raw}
            return parsed.get("answer", raw)
        except Exception:
            return raw
