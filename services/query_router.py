import re
from enum import Enum
from typing import Optional, Dict, Any, List

class QueryIntent(str, Enum):
    SPECIFIC_FACT = "SPECIFIC_FACT"
    GLOBAL_SUMMARY = "GLOBAL_SUMMARY"
    MULTI_DOC_COMPARE = "MULTI_DOC_COMPARE"

class QueryIntentRouterService:

    GLOBAL_SUMMARY_REGEX = re.compile(
        r"\b(?:summarize|summarise|summary|overview|main themes|key themes|gist|takeaways|"
        r"whole document|entire document|full document|all pages|comprehensive summary|"
        r"executive summary|what is this (?:pdf|file|document|resume|paper|notes) about|"
        r"tell me about this (?:pdf|file|document|resume)|give me a brief of)\b",
        re.IGNORECASE
    )

    MULTI_DOC_COMPARE_REGEX = re.compile(
        r"\b(?:compare|comparison|difference between|differences between|versus|\bvs\b|"
        r"which document|contrast between|compare the two|compare both)\b",
        re.IGNORECASE
    )

    @classmethod
    def classify_query_intent(
        cls,
        user_query_text: str,
        filter_document_id: Optional[int] = None,
        available_documents: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        query_cleaned = user_query_text.strip().lower()

        if cls.MULTI_DOC_COMPARE_REGEX.search(query_cleaned):
            matched_doc_ids = []
            if available_documents:
                for doc in available_documents:
                    fn_base = doc.get("filename", "").lower().replace(".pdf", "").replace(".txt", "")
                    if fn_base and fn_base in query_cleaned:
                        matched_doc_ids.append(doc.get("id"))

            return {
                "intent": QueryIntent.MULTI_DOC_COMPARE,
                "confidence": 0.95,
                "routing_reason": "Query contains comparative terms across multiple documents.",
                "matched_doc_ids": matched_doc_ids or ([d.get("id") for d in (available_documents or [])[:2]])
            }

        if cls.GLOBAL_SUMMARY_REGEX.search(query_cleaned):
            return {
                "intent": QueryIntent.GLOBAL_SUMMARY,
                "confidence": 0.96,
                "routing_reason": "Query requests high-level document synopsis spanning full content.",
                "target_document_id": filter_document_id
            }

        return {
            "intent": QueryIntent.SPECIFIC_FACT,
            "confidence": 0.90,
            "routing_reason": "Query requests specific factual detail; routed to hybrid search and reranking.",
            "target_document_id": filter_document_id
        }
