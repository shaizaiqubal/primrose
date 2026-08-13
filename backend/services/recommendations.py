import logging
import time
import redis
import json
from pathlib import Path
from fastapi.encoders import jsonable_encoder
from google import genai
from pydantic import BaseModel, model_validator
from backend.app.models import Documents
from backend.services.search import RankedDocument
from backend.app.config import GEMINI_API_KEY
from backend.app.cache import cache, TTL

logger = logging.getLogger(__name__)

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as exc:
    client = None
    logger.exception("Failed to initialize Gemini client: %s", exc)

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system_prompt.txt"

system_prompt = SYSTEM_PROMPT_PATH.read_text('utf-8')

class QueryPaper(BaseModel):
    paper_id: int
    title: str
    abstract: str


class Candidate(BaseModel):
    paper_id: int
    title: str
    abstract: str
    relevance_score: float


class RecommendInput(BaseModel):
    query_paper: QueryPaper
    candidates: list[Candidate]


class RecommendEntry(BaseModel):
    paper_id: int
    position: int
    recommendation_note: str


class RecomendationResponse(BaseModel):
    recommended: list[RecommendEntry]

    @model_validator(mode="after")
    def check_shape(self) -> "RecomendationResponse":
        if len(self.recommended) != 5:
            raise ValueError(f"Expected 5 entries, got {len(self.recommended)}.")
        if len({e.paper_id for e in self.recommended}) != 5:
            raise ValueError("Duplicate paper_id in journey.")
        return self

    
class RecommendedPaper(BaseModel):
    id: int
    arxiv_id: str | None = None
    title: str
    abstract: str
    authors: str | None
    year_published: int | None
    url: str | None
    categories: str | None = None

    relevance_score: float
    position: int
    recommendation_note: str


def recommendation_engine(query: Documents, candidates: list[RankedDocument]) -> list[RecommendedPaper]:

    key = "recommend:"+str(query.id)
    try:
        payload = cache.get(key)
    except redis.RedisError as exc:
            payload = None
            logger.warning("Redis cache unavailable for id %s: %s", query.id, exc)
    if payload:
        logger.info("Cache hit for key %s", key)
        cached_papers = jsonable_encoder(json.loads(payload))
        return [RecommendedPaper.model_validate(item) for item in cached_papers]

    logger.info("Cache miss for key %s", key)

    logger.info("Starting recommendation generation for paper %s", query.id)

    try:
        query_doc = QueryPaper(
            paper_id=query.id,
            title=query.title,
            abstract=query.abstract,
        )
        candidate_docs = [
            Candidate(
                paper_id=c.document.id,
                title=c.document.title,
                abstract=c.document.abstract,
                relevance_score=c.relevance_score,
            )
            for c in candidates
        ]

        payload = RecommendInput(query_paper=query_doc, candidates=candidate_docs)

        if client is None:
            raise RuntimeError("Gemini client is not initialized")

        start_time = time.perf_counter()
        interaction = client.interactions.create(
            model="gemini-3.1-flash-lite",
            input=f"""
                Below is the current paper and a list of candidate papers.

                The data is provided as JSON.

                {payload.model_dump_json(indent=2)}
                """,
            system_instruction=system_prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": RecomendationResponse.model_json_schema(),
            },
        )
        latency_seconds = time.perf_counter() - start_time
        logger.info(
            "Gemini request for paper %s completed in %.3f seconds",
            query.id,
            latency_seconds,
        )

        recommended = RecomendationResponse.model_validate_json(interaction.output_text)  # type: ignore

        candidate_lookup = {candidate.document.id: candidate for candidate in candidates}
        recommended_papers = []

        for entry in recommended.recommended:
            matched_candidate = candidate_lookup.get(entry.paper_id)
            if matched_candidate is None:
                raise ValueError(
                    f"Recommended paper id {entry.paper_id} was not found in the candidate list"
                )

            recommended_papers.append(
                RecommendedPaper(
                    id=matched_candidate.document.id,
                    arxiv_id=matched_candidate.document.arxiv_id,
                    title=matched_candidate.document.title,
                    abstract=matched_candidate.document.abstract,
                    authors=matched_candidate.document.authors,
                    year_published=matched_candidate.document.year_published,
                    url=matched_candidate.document.url,
                    categories=matched_candidate.document.categories,
                    relevance_score=matched_candidate.relevance_score,
                    position=entry.position,
                    recommendation_note=entry.recommendation_note,
                )
            )

        payload = json.dumps(jsonable_encoder(recommended_papers))
        try:
            cache.set(key, payload, ex=TTL)
        except redis.RedisError as exc:
            logger.warning("Failed to cache recommendations for key %s: %s", key, exc)
        else:
            logger.info("Cached recommendations for key %s (ttl=%s)", key, TTL)

        return recommended_papers

    except Exception as exc:
        logger.exception("Recommendation generation failed for paper %s: %s", query.id, exc)
        raise
