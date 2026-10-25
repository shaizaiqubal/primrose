from pydantic import BaseModel, Field, EmailStr
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