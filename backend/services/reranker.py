from sentence_transformers import CrossEncoder
from backend.app.models import Documents
from dataclasses import dataclass

cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

@dataclass
class RankedDocument:
    document : Documents
    relevance_score : float

def rerank(query: str, candidates: list[Documents]) -> list[RankedDocument]:
    pairs = []
    for candidate in candidates:
        pair = (query, candidate.title + "\n\n" + candidate.abstract)
        pairs.append(pair)

    relevance_scores = cross_encoder.predict(pairs)

    ranked_docs = sorted(
        zip(relevance_scores, candidates), 
        reverse=True,
        key= lambda x: x[0]
        )
    
    return [
        RankedDocument(candidate, float(score))
        for score, candidate in ranked_docs
    ]