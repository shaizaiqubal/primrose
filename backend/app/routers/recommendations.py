from fastapi import APIRouter, HTTPException, status

from backend.app.schemas import RankedDocumentResponse, RecommendedPaperResponse
from backend.services.reranker import RankedDocument
from backend.services.recommendations import RecommendedPaper, recommendation_engine
from backend.services.search import get_document_service, get_related


router = APIRouter(prefix="/documents", tags=["recommendations"])


@router.get("/{id}/related", response_model=list[RankedDocumentResponse])
def get_related_documents(id: int) -> list[RankedDocument]:
    return get_related(id)


@router.get("/{id}/recommendations", response_model=list[RecommendedPaperResponse])
def get_recommendations(id: int) -> list[RecommendedPaper]:
    try:
        query_doc = get_document_service(id)
        candidates = get_related(id)
        return recommendation_engine(query_doc, candidates)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Recommendation generation failed: {exc}",
        ) from exc