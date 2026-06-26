# Primrose -- Architecture

## Overview

Primrose uses a dual-store architecture: PostgreSQL holds structured document metadata and Qdrant holds vector embeddings. These two stores are kept separate by design and coordinated at query time by the FastAPI layer. A background worker handles embedding generation independently of the request cycle.

---

## Component Map

```
primrose/
  backend/
    app/
      main.py          -- FastAPI app, route definitions
      models.py        -- SQLAlchemy ORM models
      schemas.py       -- Pydantic request/response schemas
      database.py      -- DB session and engine setup
      services/
        embed.py       -- Embedding logic (SentenceTransformer)
        vector_store.py -- Qdrant client wrapper
      worker/
        worker.py      -- Background embedding worker
  frontend/
    src/
      App.jsx          -- Root component and routing
      api.js           -- Axios API client
      components/      -- UI components
    public/fonts/      -- Anvers typeface
  seed_data.py         -- Corpus ingestion script
  primrose_seed_data.json -- Seed corpus (~500 papers)
  docker-compose.yaml  -- Service orchestration
```

---

## Services

| Service   | Image          | Port  | Role                              |
|-----------|----------------|-------|-----------------------------------|
| db        | postgres:15    | 5432  | Document metadata storage         |
| qdrant    | qdrant/qdrant  | 6333  | Vector storage and ANN search     |
| backend   | (built)        | 8000  | FastAPI API + embedding worker    |
| frontend  | (built)        | 5173  | React UI via Vite                 |

---

## Dataflow

### Ingestion

```
primrose_seed_data.json
        |
   seed_data.py
        |
     [POST /documents]
        |
        +-----> PostgreSQL
        |       stores: title, abstract, authors, arxiv_url, id
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
                 stores: vector, document_id
```

The worker polls for documents that have been stored in PostgreSQL but not yet embedded. Embedding is decoupled from ingestion so the API never blocks on model inference.

---

### Semantic Search

```
User query (string)
        |
     React (App.jsx / api.js)
        |
  GET /documents/search?q=...
        |
     main.py (FastAPI)
        |
     embed.py
     (query -> vector)
        |
  vector_store.py
  (Qdrant ANN search -> top-k IDs, ranked by cosine similarity)
        |
  PostgreSQL
  (fetch metadata for top-k IDs, ordered to match Qdrant ranking)
        |
  JSON response (ordered results)
        |
     React
     (renders results with relevance scores)
```

The SQL fetch preserves the rank order returned by Qdrant. Results are not re-sorted by any database field, so retrieval order reflects semantic similarity end to end.

---

### Related Paper Discovery

```
Document ID
        |
  GET /documents/{id}/related
        |
     main.py
        |
  vector_store.py
  (fetch stored vector for document_id)
        |
  Qdrant ANN search
  (vector -> top-k similar IDs, excluding self)
        |
  PostgreSQL
  (metadata lookup, Qdrant order preserved)
        |
  JSON response
        |
     React
```

Related paper discovery reuses the same pipeline as search. The only difference is the query vector: instead of embedding a user string, it uses the pre-stored vector for the requested document.

---

## Embedding Pipeline Detail

```
Input: title + abstract (concatenated string)
        |
SentenceTransformer
(all-MiniLM-L6-v2, default Stage 1)
        |
384-dimensional float vector
        |
Qdrant upsert
(collection: "papers", payload: {document_id})
```

The model encodes title and abstract together as a single string. This gives the embedding access to both the topic signal in the title and the methodological detail in the abstract.

---

## Key Design Decisions

**Why two stores?** PostgreSQL handles relational queries, filtering, and structured retrieval efficiently. Qdrant handles approximate nearest-neighbor search at scale with built-in HNSW indexing. Using one store for both would mean either slow vector search in a general-purpose database or losing relational query capability in a vector store.

**Why a background worker?** Transformer inference is not fast enough to run inline with a write request at any meaningful scale. The worker decouples ingestion throughput from embedding latency. Documents are available for metadata queries immediately after ingestion; they become searchable once the worker embeds them.

**Why pre-seed the corpus?** A cold-start system with no documents returns no results and demonstrates nothing. Seeding ~500 papers at startup makes the application immediately usable and lets the retrieval quality be evaluated from the first request.

**Why preserve Qdrant ranking in the SQL lookup?** PostgreSQL does not guarantee row return order without an explicit ORDER BY. If the metadata fetch re-sorted results by, say, ingestion date or title, the semantic ranking from Qdrant would be silently discarded. The ordering step is explicit and intentional.