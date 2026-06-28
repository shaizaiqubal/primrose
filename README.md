# Primrose

> Research intelligence. Starting with discovery.

![Primrose](./assets/hero.png)

![Stage](https://img.shields.io/badge/stage-1%20of%207-rose?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/python-3.13-blue?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.2.7-61DAFB?style=flat-square&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/docker-compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey?style=flat-square)

🌸 **Live application:** https://primroses.vercel.app

Primrose is being built toward a single goal: making the hidden structure of scientific literature visible. Connections between ideas, clusters of related work, emerging research fronts, entity relationships, knowledge graphs: the kind of intelligence that currently lives only in the heads of domain experts.

Stage 1 is the foundation. Semantic search and related-paper discovery, powered by transformer embeddings, deployable in one command.

---

## Stages

| Stage | Status | Capability |
|-------|--------|------------|
| 1 | **Complete** | Semantic Discovery Foundation |
| 2 | Planned | Recommendation Engine |
| 3 | Planned | Topic Discovery |
| 4 | Planned | Entity Extraction |
| 5 | Planned | Relationship Discovery |
| 6 | Planned | Knowledge Graph |
| 7 | Planned | Research Intelligence Platform |

---

## Stage 1 -- Semantic Discovery Foundation

Keyword-based search breaks down at the boundaries of language. Two papers on the same idea can share almost no vocabulary. Primrose embeds papers into a vector space using transformer models, making similarity a matter of meaning rather than surface form.

**What Stage 1 delivers:**

- Semantic search over a seeded corpus of ~500 papers
- Related paper discovery per document
- Transformer embeddings via Sentence Transformers (all-MiniLM-L6-v2)
- Background worker for asynchronous embedding generation
- PostgreSQL for structured metadata storage
- Qdrant for vector storage and approximate nearest-neighbor search
- arXiv links on all documents
- Docker Compose deployment


---
 

## Evaluation

**Dataset:** 10 manually selected query papers

| Metric | Score |
|--------|-------|
| Precision@5 | 0.86 |
| MRR | 0.95 |

Most queries retrieved highly relevant papers with strong topical alignment. Occasional topic drift occurs at the edges of closely related ML subfields -- expected behavior for a general-purpose embedding model at Stage 1. Retrieval quality will improve in later stages through domain-specific models and a reranking layer.

---

## Architecture

```
            React
              |
         FastAPI API
      +--------+---------+
      |                  |
 PostgreSQL           Qdrant
 Metadata         Vector Embeddings
      ^                  ^
      +------ Worker ----+
          SentenceTransformer
```

The worker runs independently of the request cycle, pulling documents from PostgreSQL and writing embeddings to Qdrant. The API coordinates both stores at query time.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full dataflow diagrams.

---

## Retrieval Pipeline

```
Query string
  |
Embedding model
  |
Qdrant ANN search
  |
Top-k IDs (ranked by cosine similarity)
  |
PostgreSQL metadata lookup
(order preserved from Qdrant)
  |
Ordered results
```

The SQL lookup preserves the rank order returned by Qdrant. Results are not re-sorted by any database field -- retrieval order reflects semantic relevance end to end.

---

## Tech Stack

**Frontend** -- React, Vite, Axios

**Backend** -- FastAPI, SQLAlchemy, PostgreSQL, Qdrant, Sentence Transformers

**Infrastructure** -- Docker, Docker Compose

---

## Design Decisions

**Separate stores for metadata and vectors.** PostgreSQL handles structured metadata; Qdrant handles approximate nearest-neighbor search with HNSW indexing. Each store is used for what it does well.

**Background embedding worker.** Embedding generation does not block the request cycle. Documents are available for metadata queries immediately after ingestion and become searchable once the worker processes them.

**Semantic search over keyword matching.** The same concept appears under dozens of names in the research literature. Embedding-based retrieval captures intent rather than surface terms.

**Pre-embedded corpus.** Documents are seeded and embedded at startup so the application is immediately usable without a cold-start period.


---

## Running Locally

1. Create environment file:

```bash
cp backend/.env.example backend/.env
```

2. Start the development stack:

```bash
docker compose up --build
```

This starts:

| Service  | URL                        |
| -------- | -------------------------- |
| Frontend | http://localhost:5173      |
| API      | http://localhost:8000      |
| API Docs | http://localhost:8000/docs |

### Background Worker

The Docker Compose stack includes a background worker that continuously embeds newly added papers into Qdrant.

> **Deployment note:** The public demo performs embedding synchronously because Render's free tier does not support background worker services. The project retains a dedicated worker architecture for production deployments.
---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /documents | List all documents |
| GET | /documents/{id} | Retrieve a single document |
| GET | /documents/search | Semantic search |
| GET | /documents/{id}/related | Related paper discovery |
| POST | /documents | Ingest a new document |
| PUT | /documents/{id} | Update document metadata |
| DELETE | /documents/{id} | Remove a document |

`POST`, `PUT`, and `DELETE` currently serve developer and admin workflows and are not exposed in the frontend.

---

## Known Limitations (Stage 1)

- General-purpose embedding model; no domain-specific tuning or reranking
- No user authentication or access control
- Frontend is read-only; corpus management requires direct API access
- Fixed corpus with no ingestion UI
- Relevance scores not yet fully surfaced in the frontend

---

## What's Next 

- arXiv ID as a first-class schema field
- Relevance and similarity scores throughout the pipeline and frontend
- Domain-specific embedding model (SPECTER2)
- User authentication and corpus management interface
- Recommendation engine (Stage 2)

---

## License

[CC BY-NC 4.0](./LICENSE) -- free to use and adapt, not for commercial purposes.