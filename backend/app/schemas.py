from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from typing import Literal

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

class EntityResponse(BaseModel):
    id: int
    canonical_name: str
    type: str
    aliases: list[str]

    model_config = {
        "from_attributes": True
    }

class EntityPageResponse(BaseModel):
    items: list[EntityResponse]
    total: int
    page: int
    page_size: int

class EntitySearchResult(EntityResponse):
    score: float

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

class TopicResponse(BaseModel):
    topic_id: int = Field(validation_alias="cluster_id")
    topic_name: str | None = Field(validation_alias="cluster_name")
    paper_count: int


    model_config = {
            "from_attributes": True
        }

class EmailRequest(BaseModel):
    email: EmailStr

class UserCreate(BaseModel):
    email : EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = {
        "from_attributes": True
    }

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CorpusCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    categories: list[str] = Field(min_length=1)
    document_limit: int = Field(ge=500, le=10000)
    sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] = "submittedDate"
    sort_order: Literal["ascending", "descending"] = "ascending"
    start_date: date | None = None
    end_date: date | None = None
    source: str = "arxiv"


class CorpusUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    categories: list[str] | None = Field(default=None, min_length=1)
    document_limit: int | None = Field(default=None, ge=500, le=10000)
    sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] | None = None
    sort_order: Literal["ascending", "descending"] | None = None
    start_date: date | None = None
    end_date: date | None = None


class CorpusResponse(BaseModel):
    id: int
    name: str
    source: str
    categories: list[str]
    document_limit: int
    sort_by: str
    sort_order: str
    start_date: date | None
    end_date: date | None
    last_synced: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CorpusSyncRequest(BaseModel):
    pass


class CorpusSyncResponse(BaseModel):
    id: int
    corpus_id: int
    status: str
    papers_discovered: int
    papers_inserted: int
    existing_papers_skipped: int
    processing_jobs_enqueued: int
    errors_encountered: int
    started_at: datetime | None
    completed_at: datetime | None
    error_details: str | None
    upper_cutoff: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
