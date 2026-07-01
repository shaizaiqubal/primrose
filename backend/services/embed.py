from functools import lru_cache

from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")

def embed_content(title="", abstract=""):
    content = title + "\n\n" + abstract
    embedding = get_model().encode(content)
    return embedding
