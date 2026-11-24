import math
import re
import zlib
from typing import List

EMBEDDING_DIMENSION = 384

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "he", "in", "is", "it", "its", "of", "on", "that", "the", "to", "was",
    "were", "will", "with", "this", "what", "when", "where", "which", "who",
    "whom", "whose", "why", "how", "can", "could", "should", "would", "do",
    "does", "did", "have", "had", "or", "but", "not", "if", "then", "else",
    "there", "their", "they", "them", "we", "our", "you", "your", "me", "my",
}

_SYNONYM_GROUPS = [
    {"summary", "summarize", "summerize", "overview", "brief", "abstract", "recap", "highlights", "takeaways"},
    {"resume", "cv", "profile", "bio", "curriculum", "experience", "skills", "qualifications"},
    {"quiz", "test", "exam", "assessment", "mcq", "questions", "evaluation"},
    {"ai", "artificial", "intelligence", "llm", "genai", "gemini"},
    {"ml", "machine", "learning", "neural", "model", "training"},
    {"db", "database", "sql", "postgres", "postgresql", "pgvector", "storage"},
    {"auth", "authentication", "login", "signin", "signup", "otp", "token", "jwt", "password"},
    {"pdf", "document", "file", "manual", "syllabus", "notes", "report", "paper"},
    {"compare", "comparison", "difference", "differences", "versus", "vs", "contrast"},
    {"fast", "quick", "speed", "latency", "performance", "benchmark"},
    {"error", "bug", "issue", "fail", "failed", "crash", "exception"},
]

_CONCEPT_LOOKUP = {}
for idx, group in enumerate(_SYNONYM_GROUPS):
    concept_tag = f"__concept_{idx}__"
    for term in group:
        _CONCEPT_LOOKUP[term] = concept_tag


def _simple_stem(word: str) -> str:
    if len(word) <= 4:
        return word
    for suffix in ("ation", "ment", "ness", "able", "ible", "ing", "ies", "es", "ed", "ly", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            if suffix == "ies":
                return word[:-3] + "y"
            return word[: -len(suffix)]
    return word


def _project_feature(vector: List[float], feature_bytes: bytes, weight: float) -> None:
    h1 = zlib.crc32(feature_bytes) & 0xFFFFFFFF
    bucket = h1 % EMBEDDING_DIMENSION
    sign = 1.0 if ((h1 >> 16) & 1) == 0 else -1.0
    vector[bucket] += sign * weight


def _compute_384d_vector(text: str) -> List[float]:
    vector = [0.0] * EMBEDDING_DIMENSION
    clean_text = (text or "").lower().strip()
    if not clean_text:
        vector[0] = 1.0
        return vector

    raw_tokens = re.findall(r"[a-z0-9]+", clean_text)
    filtered_tokens = [tok for tok in raw_tokens if len(tok) > 1 and tok not in _STOPWORDS]
    if not filtered_tokens:
        filtered_tokens = raw_tokens or ["empty"]

    # Sublinear TF counts avoid long-chunk dominance
    token_counts = {}
    for tok in filtered_tokens:
        token_counts[tok] = token_counts.get(tok, 0) + 1

    for tok, count in token_counts.items():
        tf_weight = 1.0 + math.log(count)
        length_boost = 1.25 if len(tok) >= 5 else 1.0

        # 1. Exact token
        _project_feature(vector, f"w:{tok}".encode("utf-8"), 2.0 * tf_weight * length_boost)

        # 2. Stemmed root
        stem = _simple_stem(tok)
        _project_feature(vector, f"s:{stem}".encode("utf-8"), 1.5 * tf_weight)

        # 3. Domain concept expansion
        concept = _CONCEPT_LOOKUP.get(tok) or _CONCEPT_LOOKUP.get(stem)
        if concept:
            _project_feature(vector, concept.encode("utf-8"), 1.6 * tf_weight)

        # 4. Character 3-grams and 4-grams for typo/morphology resilience
        if len(tok) >= 4:
            padded = f"<{tok}>"
            for i in range(len(padded) - 2):
                _project_feature(vector, f"c3:{padded[i:i+3]}".encode("utf-8"), 0.35 * tf_weight)
            for i in range(len(padded) - 3):
                _project_feature(vector, f"c4:{padded[i:i+4]}".encode("utf-8"), 0.45 * tf_weight)

    # 5. Word bigrams for phrase fidelity
    for i in range(len(filtered_tokens) - 1):
        bigram = f"b:{filtered_tokens[i]}_{filtered_tokens[i+1]}".encode("utf-8")
        _project_feature(vector, bigram, 1.4)

    norm = math.sqrt(sum(v * v for v in vector))
    if norm <= 1e-12:
        vector[0] = 1.0
        return vector

    inv_norm = 1.0 / norm
    return [round(v * inv_norm, 6) for v in vector]


class VectorEmbeddingGenerator:
    """
    Lightweight, zero-OOM 384-dimensional semantic feature-hashing embedder.
    Compatible with PostgreSQL pgvector Vector(384) without PyTorch memory overhead.
    """

    cached_model_instance = None

    @classmethod
    def get_or_load_model(cls):
        return cls

    @classmethod
    def generate_single_embedding(cls, input_text_string: str) -> List[float]:
        return _compute_384d_vector(input_text_string)

    @classmethod
    def generate_batch_embeddings(cls, list_of_text_strings: List[str]) -> List[List[float]]:
        if not list_of_text_strings:
            return []
        return [_compute_384d_vector(text) for text in list_of_text_strings]
