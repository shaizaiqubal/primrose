from backend.services.vector_store import get_related_ids, query_documents
from backend.services.reranker import rerank, RankedDocument
from backend.services.embed import embed_content
from backend.app.models import Documents
from backend.app.database import SessionLocal
from sqlalchemy import select,case
from fastapi import HTTPException, status
from collections.abc import Sequence


def _get_document_or_404(db, id: int) -> Documents:
    stmt = select(Documents).where(Documents.id == id)
    result = db.execute(stmt).scalar_one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return result


def get_document_service(id: int) -> Documents:
    with SessionLocal() as db:
        return _get_document_or_404(db, id)

def document_to_query(document: Documents) -> str:
    parts = [part for part in (document.title, document.abstract) if part]
    return "\n\n".join(parts)


def fetch_candidates(related_ids: Sequence[object]) -> list[Documents]:
    if not related_ids:
        print("[search] fetch_candidates: no related_ids provided")
        return []

    candidate_ids = list(related_ids)
    print(f"[search] fetch_candidates: requested={len(candidate_ids)} ids={candidate_ids}")

    with SessionLocal() as db:
        order = case(
            {doc_id: idx for idx, doc_id in enumerate(candidate_ids)},
            value=Documents.id
        )
        stmt = select(Documents).where(Documents.id.in_(candidate_ids)).order_by(order)
        documents = list(db.execute(stmt).scalars().all())

    found_ids = [doc.id for doc in documents]
    missing_ids = [doc_id for doc_id in candidate_ids if doc_id not in found_ids]
    print(
        f"[search] fetch_candidates: found={len(documents)} ids={found_ids} missing={missing_ids}"
    )
    return documents

def search(query: str) -> list[RankedDocument]:
    query_embed = embed_content(abstract=query)
    try:
        related_ids = query_documents(query_embed)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vector store query failed: {e}"
        )

    if not related_ids:
        print("[search] search: query_documents returned no ids")
        return []

    print(f"[search] search: query_documents returned {len(related_ids)} ids={related_ids}")
    related = fetch_candidates(related_ids)
    print(f"[search] search: reranking {len(related)} fetched candidates")

    ranked_documents = rerank(query, related)   
    print(f"[search] search: rerank returned {len(ranked_documents)} results")
        
    return ranked_documents

def get_related(id: int) -> list[RankedDocument]:
    with SessionLocal() as db:
        query_doc = _get_document_or_404(db, id)
    
    query = document_to_query(query_doc)
    try:
        related_ids = get_related_ids(id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve related documents: {e}"
        )

    if not related_ids:
        return []

    related = fetch_candidates(related_ids)

    ranked_documents = rerank(query, related)   
        
    return ranked_documents
