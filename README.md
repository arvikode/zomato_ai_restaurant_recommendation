# AI Restaurant Recommendation System

Proof of Concept AI Restaurant Recommendation system. Internal demo only.

## Architecture

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** React (Vite)
- **LLM:** Gemini (default) with xAI Grok fallback; optional Ollama (Phase 3)

See [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md) for full details.

## Phase-Based Build

| Phase | Description |
|-------|-------------|
| 0 | Repo structure, env, dependencies |
| 1 | Data ingestion (HuggingFace → PostgreSQL) |
| 2 | Backend API (deterministic filtering) |
| 3 | LLM recommendation layer (Gemini + Grok fallback, or Ollama) |
| 4 | Frontend demo UI |

## Non-Goals

- Payments, ordering, real-time availability
- Scaling beyond ~50 users
- Authentication

## Prerequisites

- Python 3.11+
- Node 18+ (Phase 4)

**Database:** SQLite by default (no setup). Data auto-loads from HuggingFace on first server start.

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for tests

# Copy env template
cp .env.example .env
# Set GEMINI_API_KEY (primary). Set GROK_API_KEY for fallback when Gemini fails.
```

## Phase 1: Data Ingestion

Data loads automatically when you start the server (first run fetches from HuggingFace, ~1-2 min).
To run ingest manually: `python scripts/ingest_zomato_data.py`

## Phase 2: Backend API

```bash
# Start the API server (from project root)
uvicorn backend.main:app --reload

# API available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

## Terminal test (interactive)

1. **Terminal 1** — start the server:
   ```bash
   uvicorn backend.main:app --reload
   ```
2. **Terminal 2** — run the interactive test:
   ```bash
   python scripts/terminal_test.py
   ```
   You’ll be prompted to select **city**, then **price** ($ / $$ / $$$), then how many recommendations. Results are printed in the terminal.

**Endpoints:**
- `GET /cities` — distinct sorted city list
- `GET /restaurants?city=Bangalore&price_category=$$&limit=20` — filtered restaurants by rating DESC
- `POST /recommendations` — AI-ranked recommendations (Phase 3). Gemini (default) with Grok fallback; set keys in .env.

## Run Tests

```bash
# With pytest (recommended)
pytest tests/ -v

# Without pytest (fallback)
python run_tests.py
```

## Project Structure

```
├── backend/       # FastAPI app (Phase 2+)
├── frontend/      # React app (Phase 4)
├── data/          # Optional local cache
├── scripts/       # Ingest and utilities
├── tests/         # Unit tests
└── ARCHITECTURE_PLAN.md
```
