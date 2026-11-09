from typing import List
from config import settings

class VectorEmbeddingGenerator:
    cached_model_instance = None

    @classmethod
    def get_or_load_model(cls):
        if cls.cached_model_instance is None:
            from sentence_transformers import SentenceTransformer
            cls.cached_model_instance = SentenceTransformer(settings.embedding_model_name)
        return cls.cached_model_instance

    @classmethod
    def generate_single_embedding(cls, input_text_string: str) -> List[float]:
        transformer_model = cls.get_or_load_model()
        computed_vector = transformer_model.encode(input_text_string, normalize_embeddings=True)
        return computed_vector.tolist()

    @classmethod
    def generate_batch_embeddings(cls, list_of_text_strings: List[str]) -> List[List[float]]:
        if not list_of_text_strings:
            return []
        transformer_model = cls.get_or_load_model()
        computed_vectors = transformer_model.encode(
            list_of_text_strings,
            batch_size=32,
            normalize_embeddings=True
        )
        return computed_vectors.tolist()
