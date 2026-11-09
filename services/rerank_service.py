import re
from typing import List, Dict, Any

class CandidateRerankerService:
    @staticmethod
    def rerank_chunks(
        query_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        if not retrieved_chunks:
            return []

        clean_query = query_text.lower()
        query_terms = [t for t in re.findall(r"\w+", clean_query) if len(t) > 2]
        query_bigrams = []
        for i in range(len(query_terms) - 1):
            query_bigrams.append(f"{query_terms[i]} {query_terms[i+1]}")

        scored_candidates = []

        for chunk in retrieved_chunks:
            content = chunk["chunk_text_content"].lower()
            content_words = re.findall(r"\w+", content)
            total_content_words = max(len(content_words), 1)

            term_match_count = sum(1 for term in query_terms if term in content)
            term_coverage_ratio = term_match_count / max(len(query_terms), 1)

            exact_phrase_bonus = 0.3 if clean_query in content else 0.0

            bigram_match_count = sum(1 for bg in query_bigrams if bg in content)
            bigram_ratio = (bigram_match_count / max(len(query_bigrams), 1)) if query_bigrams else 0.0

            vector_similarity_ratio = chunk["similarity_percentage"] / 100.0

            lexical_score = (term_coverage_ratio * 0.5) + (bigram_ratio * 0.3) + exact_phrase_bonus
            combined_rerank_score = (vector_similarity_ratio * 0.55) + (min(1.0, lexical_score) * 0.45)

            chunk_copy = dict(chunk)
            chunk_copy["rerank_score"] = round(combined_rerank_score * 100.0, 2)
            scored_candidates.append(chunk_copy)

        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_k]
