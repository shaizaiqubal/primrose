# Primrose - Architecture

## Overview

Primrose uses PostgreSQL, Qdrant, Redis, and a FastAPI orchestration layer:
- PostgreSQL stores document metadata, ingestion state, topic assignments, and topic metadata.
- Qdrant stores document embeddings and powers approximate nearest-neighbor retrieval.
- Redis caches expensive retrieval, recommendation, and topic-read results.
- FastAPI coordinates ingestion, semantic search, related-paper discovery, recommendations, and topic APIs.

Embedding generation is handled by an asynchronous background worker. Recommendation generation is handled separately through a reranking plus LLM pipeline.

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
      topic_worker.py   -- K-Means topic discovery
      clusters.py       -- Gemini-based topic labeling
      topics.py         -- Topic read APIs and Redis caching
      queue_docs.py     -- Document job publishing
      worker.py         -- Pub/Sub-triggered embedding worker

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
| `cache` |	`redis`	| Cache for expensive API computations |
| `init_schema` | built from repo | One-shot database schema bootstrap |
| `worker` | built from repo | Processes embedding jobs delivered through Google Cloud Pub/Sub and writes vectors to Qdrant|
| `api` | built from repo | FastAPI application and orchestration layer |
| `frontend` | built from `./frontend` | React UI |

The Docker Compose stack brings up the schema initializer before the API starts. Redis is used as a shared cache by the API, including topic list and topic detail responses.

---

## Cache Architecture

Redis sits in front of the most expensive read paths in the API:

- `backend/services/topics.py` caches the topic list, individual topic details, and topic paper lists.
- `backend/services/recommendations.py` caches generated Reading Journeys per source paper.

Both code paths fall back to PostgreSQL and Gemini when cache entries are missing, and they repopulate Redis after a successful response. The cache entries use a shared TTL so hot topics and frequently requested recommendation results stay fast without becoming stale indefinitely.

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

Topic data lives in two additional tables:

- `topics`
- `document_topics`

`topics` stores the cluster identifier, generated topic name, paper count, and cluster centroid. `document_topics` maps each document to exactly one topic cluster.

Qdrant points are stored with the document ID as the point ID and a payload containing lightweight metadata such as `document_id`, `year_published`, and `authors`.

---

## Ingestion

```text

            [POST /documents]
                   |
                   v
              PostgreSQL
                   |
                   v
          Publish document ID
              to Pub/Sub
                   |
                   v
        Cloud Run Worker (Push)
                   |
                   v
              embed.py
                   |
        SentenceTransformer
       (title + abstract → vector)
                   |
                   v
          vector_store.py
                   |
                   v
                Qdrant
                   |
                   v
      PostgreSQL (embedded = true)
                 
```

After a document is stored in PostgreSQL, the API publishes its document ID to a Google Cloud Pub/Sub topic. A dedicated Cloud Run worker receives the message, generates the embedding using SentenceTransformer, writes the vector to Qdrant, and marks the document as embedded in PostgreSQL. This asynchronous pipeline keeps document ingestion responsive while allowing embedding to scale independently of the API.

The API also exposes `POST /documents/{id}/embed` for manually embedding a specific document when needed.

---

## Topic Architecture

```text
Embedded documents in Qdrant
   |
topic_worker.py
   |
K-Means clustering 
   |
topics + document_topics in PostgreSQL
   |
clusters.py
   |
Representative papers from Qdrant centroids
   |
Gemini topic labeling
   |
topics.cluster_name update
```

Topic generation is a batch workflow built on top of the embedding corpus rather than a user-facing request path.

1. `topic_worker.py` pulls up to 10,000 embedded vectors from Qdrant and clusters them with K-Means into 100 research topics.
2. It writes one `topics` row per cluster with the cluster centroid and paper count.
3. It writes `document_topics` rows to associate each document with its cluster.
4. `clusters.py` finds unnamed topics, uses each cluster centroid to fetch representative documents from Qdrant, and asks Gemini to generate a concise research topic name.
5. The generated label is stored back in `topics.cluster_name`.

The topic read APIs in `backend/services/topics.py` then serve the clustered data through `/topics`, `/topics/{topic_id}`, and `/topics/{topic_id}/papers`, with Redis caching to avoid repeated database lookups for popular topic pages.

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

**Why an asynchronous Pub/Sub worker?** Embedding generation is significantly slower than ordinary request handling. Rather than blocking API requests, the API publishes an embedding job to Google Cloud Pub/Sub. A dedicated Cloud Run worker processes the job independently, allowing ingestion to remain responsive while enabling automatic retries, independent scaling, and reliable background processing.

**Why keep an explicit `embedded` flag?** The flag makes the data flow observable and allows the worker to resume interrupted ingestion without duplicating work.

**Why rerank after ANN search?** Qdrant is good at candidate generation, while the cross-encoder is better at fine-grained relevance ordering. Using both improves result quality without forcing the vector store to do everything.

**Why a separate recommendation step?** Recommendations are not just "more similar papers". The Gemini step turns ranked candidates into an ordered reading path with short explanations.

---

## Operational Notes

- `backend/init_schema.py` creates the database tables at startup.

