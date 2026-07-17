from pydantic import BaseModel
from datetime import datetime

class Document(BaseModel):
    arxiv_id: str | None = None
    title : str
    abstract : str
    authors: str | None
    year_published: int | None
    url: str | None
    categories: str | None = None

class DocumentResponse(BaseModel):
    id: int
    arxiv_id: str | None = None
    title: str
    abstract: str
    authors: str | None
    year_published: int | None
    url: str | None
    categories: str | None = None
    created_at: datetime
    embedded: bool

    model_config = {
        "from_attributes": True
    }

class RankedDocumentResponse(BaseModel):
    document: DocumentResponse
    relevance_score: float

    model_config = {
        "from_attributes": True
    }

class RecommendedPaperResponse(BaseModel):
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
