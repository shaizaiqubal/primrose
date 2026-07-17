# Changelog

All notable changes to Primrose are documented here.

---

## Stage 1 -- Semantic Discovery Foundation

*Released: June 2026*

- Semantic search over a seeded corpus of ~500 research papers
- Related paper discovery per document
- Transformer embeddings via Sentence Transformers (all-MiniLM-L6-v2)
- Background worker for asynchronous embedding generation
- PostgreSQL for structured document metadata storage
- Qdrant for vector storage and approximate nearest-neighbor search
- FastAPI backend with full CRUD and search endpoints
- React frontend with search and related paper views
- arXiv links on all documents
- Docker Compose deployment
- Seed corpus and ingestion script (`seed_data.py`)
- Evaluation: Precision@5 0.86, MRR 0.95 on 10 manually selected query papers

---

## Stage 2 — Research Recommendations

- Added AI-powered Reading Journeys for guided paper discovery
- Introduced Cross-Encoder reranking to improve retrieval quality
- Integrated Gemini to generate contextual recommendation notes
- Added a recommendation API endpoint and backend recommendation service
- Added first-class support for arXiv IDs in the paper schema
- Improved Docker startup with automatic database schema initialization
- Refactored the retrieval pipeline into retrieval, reranking, and recommendation stages
- Expanded testing infrastructure with isolated databases and vector stores
- Updated the architecture to support scalable AI-assisted research exploration