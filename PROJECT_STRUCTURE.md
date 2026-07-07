# 📂 Project Structure Guide

This document maps out the key components, source directories, and architectural layouts of the **AI Email Suggested Response System**.

```text
.
├── backend/                     # FastAPI ASGI Server & ML Models
│   ├── main.py                  # Entry point, timing logs, lifecycles, health metrics
│   ├── database.py              # SQLite connection pool and WAL setup
│   ├── config.py                # Pydantic environment configurations
│   ├── models/                  # SQLite tables ORMs
│   ├── schemas/                 # FastAPI REST validation contracts
│   ├── routers/                 # Route handlers: CRUD, analytics, dataset, eval
│   ├── retrieval/               # RAG: sentence-transformers embeds + FAISS engine
│   ├── generator/               # Few-shot prompts, Gemini API, template fallbacks
│   └── evaluation/              # 12-metric evaluation engine + LLM Judge
│
├── frontend/                    # Next.js 15 TypeScript Dashboard
│   ├── app/                     # Cockpit page structures (Home, Dataset, generate)
│   ├── components/              # Charts, timeline, pipeline flows, score rings
│   ├── lib/                     # Type-safe API fetching and utility handlers
│   └── types/                   # Frontend model contracts
│
├── dataset/                     # Target data files and generators
│   └── generator.py             # ~1000 proportional mock data generator
│
├── scripts/                     # Operational automation scripts
│   ├── seed_db.py               # Database migrator + FAISS vector builder
│   └── test_pipeline.py         # System end-to-end operational verification tests
│
├── Dockerfile.backend           # Python 3.14 production container
├── Dockerfile.frontend          # Next.js standalone container
└── docker-compose.yml           # Unified orchestration stack
```
