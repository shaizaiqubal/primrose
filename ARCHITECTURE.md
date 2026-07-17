# Primrose - Architecture

## Overview

Primrose uses two specialized stores and a FastAPI orchestration layer:

- PostgreSQL stores document metadata and ingestion state.
- Qdrant stores document embeddings and powers approximate nearest-neighbor retrieval.
- FastAPI coordinates semantic search, related-paper discovery, and recommendation generation.

Embedding generation is handled out of band by a background worker. Recommendation generation is handled separately through a reranking plus LLM pipeline.

---

## Component Map

```text
primrose/
  backend/
    app/
      main.py           -- FastAPI routes and orchestration
      config.py         -- Environment and service configuration
      database.py       -- SQLAlchemy engine and session setup
      models.py         -- PostgreSQL ORM models
      schemas.py        -- API request/response models
    corpus/
      arxiv_client.py   -- arXiv API client
      downloader.py     -- Corpus ingestion script
    services/
      embed.py          -- SentenceTransformer embedding helper
      reranker.py       -- Cross-encoder reranking
      search.py         -- Semantic search and related-paper lookup
      vector_store.py   -- Qdrant client wrapper
      recommendations.py -- Gemini-based reading journey generation
    worker/
      worker.py         -- Polling embedding worker
  frontend/
    src/
      App.jsx           -- Root UI
      api.js            -- API client
      components/       -- Search, result, and recommendation UI
  docker-compose.yaml   -- Local service orchestration
```

---

## Services

| Service | Image | Role |
| --- | --- | --- |
| `postgres` | `postgres:17` | Persistent document metadata store |
| `qdrant` | `qdrant/qdrant:latest` | Vector database for embeddings |
| `init_schema` | built from repo | One-shot database schema bootstrap |
| `worker` | built from repo | Polls for unembedded documents and writes vectors to Qdrant |
| `api` | built from repo | FastAPI application and orchestration layer |
| `frontend` | built from `./frontend` | React UI |

The Docker Compose stack brings up the schema initializer before the API and worker start. That keeps the database creation step separate from the runtime containers.

---

## Data Model

The core document record lives in PostgreSQL and includes:

- `id`
- `arxiv_id`
- `title`
- `abstract`
- `authors`
- `year_published`
- `url`
- `categories`
- `created_at`
- `embedded`

The `embedded` flag is the coordination signal between PostgreSQL and Qdrant. A document can exist in the metadata store before its vector has been generated and written.

Qdrant points are stored with the document ID as the point ID and a payload containing lightweight metadata such as `document_id`, `year_published`, and `authors`.

---

## Ingestion

```text

     [POST /documents]
        |
        +-----> PostgreSQL
        |
        +-----> worker.py (background)
                    |
               embed.py
                    |
          SentenceTransformer
          (title + abstract -> vector)
                    |
             vector_store.py
                    |
                 Qdrant
                 
```

The worker polls for documents that have been stored in PostgreSQL but not yet embedded. Embedding is decoupled from ingestion so the API never blocks on model inference.

The API also exposes `POST /documents/{id}/embed` for manually embedding a specific document when needed.

---

## Semantic Search

```text
User query
   |
frontend
   |
GET /documents/search?q=...
   |
main.py
   |
embed.py
   |
vector_store.py
   |
Qdrant ANN search
   |
PostgreSQL metadata lookup
   |
reranker.py
   |
JSON response
```

Search works in two phases:

1. The query text is embedded with `SentenceTransformer("all-MiniLM-L6-v2")`.
2. Qdrant returns the nearest document IDs, which are then hydrated from PostgreSQL and reranked with the cross-encoder.

The retrieval order from Qdrant is preserved through the metadata lookup so the reranker always receives candidates in the intended semantic order.

---

## Related Papers

```text
Document ID
   |
GET /documents/{id}/related
   |
main.py
   |
search.py
   |
Qdrant retrieve stored vector
   |
Qdrant ANN search
   |
PostgreSQL metadata lookup
   |
reranker.py
   |
JSON response
```

Related-paper discovery reuses the same retrieval stack as search, but the query vector comes from the stored embedding for the requested document instead of from user input.

---

## Recommendations

```text
Document ID
   |
GET /documents/{id}/recommendations
   |
main.py
   |
search.py -> related candidates
   |
reranker.py
   |
recommendations.py
   |
Gemini API
   |
Reading Journey response
```

The recommendation endpoint builds on the related-paper pipeline:

- `search.py` collects a candidate set.
- `reranker.py` scores the candidates for relevance.
- `recommendations.py` sends the query paper plus candidates to Gemini.
- The model returns a structured five-step reading journey with notes and positions.

This design keeps retrieval and sequencing separate. The retriever finds relevant papers; the LLM explains what to read next and why.

---

## Embedding Pipeline

```text
title + abstract
   |
embed.py
   |
all-MiniLM-L6-v2
   |
384-dimensional vector
   |
vector_store.py
   |
Qdrant upsert
```

The embedding input is the title and abstract concatenated with a blank line between them. That gives the model both the concise topic signal in the title and the detailed context in the abstract.

Qdrant is configured with cosine distance and a vector size of 384 to match the SentenceTransformer output.

---

## Key Design Decisions

**Why PostgreSQL and Qdrant?** PostgreSQL is the system of record for structured paper metadata. Qdrant is optimized for nearest-neighbor search. Splitting them keeps each store focused on the job it does best.

**Why a background worker?** Embedding is slower than ordinary request handling, so the worker keeps request latency low and lets ingestion remain responsive.

**Why keep an explicit `embedded` flag?** The flag makes the data flow observable and allows the worker to resume interrupted ingestion without duplicating work.

**Why rerank after ANN search?** Qdrant is good at candidate generation, while the cross-encoder is better at fine-grained relevance ordering. Using both improves result quality without forcing the vector store to do everything.

**Why a separate recommendation step?** Recommendations are not just "more similar papers". The Gemini step turns ranked candidates into an ordered reading path with short explanations.

---

## Operational Notes

- `backend/init_schema.py` creates the database tables at startup.
- `backend/worker/worker.py` skips test mode unless `ENABLE_WORKER_ON_TEST_DB=1` is set.


