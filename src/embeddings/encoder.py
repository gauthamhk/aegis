import numpy as np
from sentence_transformers import SentenceTransformer

from src.utils.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

_encoder: SentenceTransformer | None = None


def get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        logger.info("embeddings.loading", model=settings.embedding_model)
        _encoder = SentenceTransformer(settings.embedding_model)
        logger.info("embeddings.loaded")
    return _encoder


def encode_texts(texts: list[str]) -> np.ndarray:
    encoder = get_encoder()
    return encoder.encode(texts, normalize_embeddings=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))
