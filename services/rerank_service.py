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
        query_terms = set(t for t in re.findall(r"\w+", clean_query) if len(t) > 2)
        query_bigrams = []
        ordered_terms = list(query_terms)
        for i in range(len(ordered_terms) - 1):
            query_bigrams.append(f"{ordered_terms[i]} {ordered_terms[i+1]}")

        scored_candidates = []

        for chunk in retrieved_chunks:
            content = chunk["chunk_text_content"].lower()
            filename = chunk.get("document_filename", "").lower()

            filename_boost = 0.0
            for term in query_terms:
                if term in filename:
                    filename_boost += 25.0

            resume_keywords = ["resume", "cv", "candidate", "skills", "projects", "intern", "experience", "education", "cgpa", "marks", "scores", "profile", "bio"]
            if any(kw in clean_query for kw in resume_keywords):
                if "resume" in filename or "cv" in filename:
                    filename_boost += 35.0

            study_keywords = ["mining", "weka", "clustering", "classification", "association", "experiment", "algorithm", "dataset", "syllabus", "lecture", "notes", "chapter", "unit"]
            if any(kw in clean_query for kw in study_keywords):
                if "dm" in filename or "notes" in filename or "syllabus" in filename or "file" in filename:
                    filename_boost += 25.0

            term_match_count = sum(1 for term in query_terms if term in content)
            term_coverage_ratio = term_match_count / max(len(query_terms), 1)

            exact_phrase_bonus = 0.3 if clean_query in content else 0.0

            bigram_match_count = sum(1 for bg in query_bigrams if bg in content)
            bigram_ratio = (bigram_match_count / max(len(query_bigrams), 1)) if query_bigrams else 0.0

            vector_similarity_ratio = chunk.get("similarity_percentage", 50.0) / 100.0

            lexical_score = (term_coverage_ratio * 0.5) + (bigram_ratio * 0.3) + exact_phrase_bonus
            base_score = (vector_similarity_ratio * 0.5) + (min(1.0, lexical_score) * 0.5)
            final_rerank_score = (base_score * 100.0) + min(filename_boost, 60.0)

            chunk_copy = dict(chunk)
            chunk_copy["rerank_score"] = round(final_rerank_score, 2)
            scored_candidates.append(chunk_copy)

        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_k]
