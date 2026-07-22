from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from backend.app.schemas import Document, DocumentResponse, RankedDocumentResponse, RecommendedPaperResponse
from backend.app.database import SessionLocal
from backend.app.models import Documents
from backend.services.vector_store import delete_embedding, insert_embedding
from backend.services.reranker import RankedDocument
from backend.services.embed import embed_content
from backend.services.search import search, get_related, get_document_service
from backend.services.recommendations import recommendation_engine, RecommendedPaper
from backend.services.queue_docs import queue_documents
from backend.app.config import FRONTEND_URL
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

app = FastAPI()

origins = ["http://localhost:5173"]
if FRONTEND_URL:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _get_document_or_404(db, id: int) -> Documents:
    stmt = select(Documents).where(Documents.id == id)
    result = db.execute(stmt).scalar_one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return result

@app.get('/')
def root() -> dict:
    return {'message' : 'Primrose.S1 server is running!'}

@app.post('/documents', response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def post_documents(request : Document) -> Documents:
    with SessionLocal() as db:
        entry = Documents(
            arxiv_id = request.arxiv_id,
            title = request.title,
            abstract = request.abstract,
            authors = request.authors,
            year_published = request.year_published,
            url = request.url,
            categories = request.categories,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        db.close()

    id = queue_documents(entry)
    logging.info(f"Published message {id}")
    return entry

@app.get('/documents', response_model=list[DocumentResponse])
def get_documents() -> list[Documents]:
    with SessionLocal() as db:
        stmt = select(Documents).order_by(Documents.id).limit(50)
        result = list(db.execute(stmt).scalars().all())
        return result

@app.get("/documents/search", response_model=list[RankedDocumentResponse])
def search_documents(query: str) -> list[RankedDocument]: 
    return search(query)

@app.get('/documents/{id}', response_model=DocumentResponse)
def get_document(id: int) -> Documents:
    return get_document_service(id)

@app.delete('/documents/{id}')
def delete_document(id: int) -> dict:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        try:
            delete_embedding(result.id)
            db.delete(result)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Delete failed: {e}"
            )
    return {'message': 'Document deleted successfully'}

@app.put('/documents/{id}', response_model=DocumentResponse)
def update_document(id: int, request: Document) -> Documents:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        result.title = request.title
        result.abstract = request.abstract
        result.authors = request.authors
        result.year_published = request.year_published
        result.url = request.url
        result.categories = request.categories
        result.arxiv_id = request.arxiv_id
        db.commit()
        db.refresh(result)
        return result

@app.post("/documents/{id}/embed")
def embed_document(id: int) -> dict:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        try:
            embedding = embed_content(title = result.title, abstract = result.abstract)
            insert_embedding(result, embedding)
            result.embedded = True
            db.commit()
            db.refresh(result)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Embedding failed: {e}"
            )
        
        return {'message': 'Embedded successfully'}
    

@app.get("/documents/{id}/related", response_model=list[RankedDocumentResponse])
def get_related_documents(id: int) -> list[RankedDocument]:
    return get_related(id)
    
@app.get("/documents/{id}/recommendations", response_model=list[RecommendedPaperResponse])
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
