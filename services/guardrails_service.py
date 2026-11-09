import re
from typing import List, Dict, Any, Tuple, Optional, Set

class HallucinationGuardrailService:

    GREETING_TOKENS = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening", "namaste", "yo", "who are you", "help"}

    @classmethod
    def evaluate_retrieval_confidence(
        cls,
        retrieved_chunks: List[Dict[str, Any]],
        query_text: str,
        confidence_threshold: float = 25.0
    ) -> Tuple[bool, Optional[str]]:
        clean_query = query_text.lower().strip()
        if any(clean_query == g or clean_query.startswith(g + " ") for g in cls.GREETING_TOKENS):
            return False, None

        if not retrieved_chunks:
            return True, "I couldn't find sufficient evidence in the uploaded documents to answer this reliably. Please confirm that the target document is uploaded."

        best_score = max([
            chunk.get("similarity_percentage", 0.0)
            for chunk in retrieved_chunks
        ])

        if best_score < confidence_threshold:
            return True, (
                "I couldn't find sufficient evidence in the uploaded documents to answer this reliably. "
                f"The highest contextual similarity score was only {best_score}%, which is below the minimum required "
                f"confidence threshold ({confidence_threshold}%)."
            )

        return False, None

    @classmethod
    def verify_and_align_citations(
        cls,
        answer_text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        valid_pages: Set[int] = set()
        for chunk in retrieved_chunks:
            p_num = chunk.get("source_page_number")
            if p_num is not None:
                valid_pages.add(int(p_num))

        cited_page_matches = re.findall(r"\[Page\s*(\d+)\]|Page\s*(\d+)", answer_text, re.IGNORECASE)
        found_pages = set()
        for m1, m2 in cited_page_matches:
            target_str = m1 or m2
            if target_str:
                found_pages.add(int(target_str))

        verified_pages = found_pages.intersection(valid_pages)
        unverified_pages = found_pages.difference(valid_pages)

        citation_metadata = {
            "retrieved_context_pages": sorted(list(valid_pages)),
            "cited_pages": sorted(list(found_pages)),
            "verified_pages": sorted(list(verified_pages)),
            "unverified_pages": sorted(list(unverified_pages)),
            "citation_integrity": len(unverified_pages) == 0
        }

        if unverified_pages:
            sanitized_answer = answer_text
            for bad_p in unverified_pages:
                sanitized_answer = re.sub(
                    rf"\[Page\s*{bad_p}\]",
                    f"[Page {bad_p} (Unverified)]",
                    sanitized_answer
                )
            return sanitized_answer, citation_metadata

        return answer_text, citation_metadata
