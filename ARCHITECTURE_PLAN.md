# AI Restaurant Recommendation System — Architecture Plan

## Overview

This document describes the architecture for a Proof of Concept AI Restaurant Recommendation system. **Phases 0–4 are implemented.**

---

## Constraints

- Standalone internal demo
- Max ~50 users; no scaling concerns
- Code clarity > optimization
- Simple, readable implementations
- No premature abstractions
- All configuration via environment variables; no hardcoded secrets
- **Out of scope:** payments, ordering, real-time availability

---

## Implementation Status (as of Phase 3)

| Phase | Status | Notes |
|-------|--------|--------|
| 0 | Done | Repo structure, SQLite default, .env.example |
| 1 | Done | HuggingFace ingest, transform logic, auto-load on startup |
| 2 | Done | GET /cities, GET /restaurants, unit tests |
| 3 | Done | POST /recommendations (Grok), unit tests |
| 4 | Done | React frontend |

---

## Phase 0 — Repository & Tech Stack Setup

### 1. Monorepo Structure (Implemented)

```
/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── ingest.py           # Shared ingest logic (used by startup + script)
│   ├── llm/
│   │   ├── client.py
│   │   └── prompts.py
│   └── routers/
│       ├── cities.py
│       ├── restaurants.py
│       └── recommendations.py
├── frontend/               # Phase 4
├── data/                   # SQLite DB and cache
│   └── restaurants.db     # Created automatically, gitignored
├── scripts/
│   ├── ingest_zomato_data.py
│   └── transform.py
├── tests/
│   ├── test_transform.py
│   ├── test_ingest.py
│   ├── test_backend.py
│   └── test_recommendations.py
├── README.md
├── .env.example
├── .env                    # Copy from .env.example; not in git
├── validate.sh
├── run_tests.py
└── ARCHITECTURE_PLAN.md
```

### 2. Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, **SQLite (default)**, python-dotenv, httpx |
| Database | SQLite file `data/restaurants.db`; optional PostgreSQL via `DATABASE_URL` |
| Frontend | React (Vite) — Phase 4 |
| Auth | None |

### 3. Environment Variables

**`.env.example`** (template; copy to `.env` and edit):

```env
# Database - SQLite by default (no setup). Set DATABASE_URL for PostgreSQL.
# DATABASE_URL=postgresql://user:pass@localhost:5432/zomato_ai

# LLM (xAI Grok) - set your key for POST /recommendations
GROK_API_KEY=dummy-key-replace-me
GROK_MODEL=grok-beta
GROK_BASE_URL=https://api.x.ai/v1

# Frontend - Phase 4
VITE_API_URL=http://localhost:8000
```

**Important:** The app reads **`.env`**, not `.env.example`. Create `.env` with `cp .env.example .env` and set `GROK_API_KEY`.

### 4. Backend Entry Point

- **Path:** `backend/main.py`
- **Run from project root:** `uvicorn backend.main:app --reload`

---

## Phase 1 — Data Preprocessing & Ingestion (Implemented)

### 1. Dataset Source

- **HuggingFace:** `ManikaSaini/zomato-restaurant-recommendation`
- **Size:** ~51.7k rows

### 2. Database: SQLite by Default

- **Default:** `data/restaurants.db` (created automatically; no setup).
- **Optional:** Set `DATABASE_URL` in `.env` for PostgreSQL.
- **Schema:** Uses SQLAlchemy `JSON` (not PostgreSQL `JSONB`) for `raw_data` so the same code works with SQLite and PostgreSQL.

### 3. Auto-Load on Server Startup

- On startup, if the `restaurants` table is empty, the app runs the ingest (loads from HuggingFace). First start takes ~1–2 minutes.
- Subsequent starts use existing data. To re-ingest: `python scripts/ingest_zomato_data.py`.

### 4. Shared Ingest Logic

- **`backend/ingest.py`:** `run_ingest()`, `is_db_empty()` — used by startup and by the script.
- **`scripts/ingest_zomato_data.py`:** Calls `run_ingest()`; can be run manually.
- **`scripts/transform.py`:** Pure normalization and `transform_row()`; fully unit-tested.

### 5. Normalization Rules (Implemented)

| Field | Rules |
|-------|-------|
| **City** | Trim, title-case; "Bengaluru" → "Bangalore"; drop rows where city is null/empty |
| **Rating** | Parse "4.1/5" → float; invalid → NULL |
| **Cost** | Parse to int; "800, 900" → take first; missing/zero → NULL |
| **Price category** | &lt;500→$, 500–1500→$$, &gt;1500→$$$; skip row if cost_for_two is NULL |
| **Online order** | Yes→true, No→false |

### 6. Testing (Phase 1)

- **`tests/test_transform.py`:** Unit tests for all normalization functions.
- **`tests/test_ingest.py`:** Unit tests for `transform_row()`.
- **`run_tests.py`:** Fallback runner when pytest is not installed.

---

## Phase 2 — Backend API (Implemented)

### 1. Endpoints

| Method | Path | Params / Body | Description |
|--------|------|----------------|-------------|
| GET | `/` | — | Health check |
| GET | `/cities` | — | Distinct sorted city list |
| GET | `/restaurants` | `city`, `price_category` ($, $$, $$$), `limit` (default 20) | Filtered list, order by rating DESC |
| POST | `/recommendations` | Phase 3 |

### 2. Response Models (Pydantic)

- **RestaurantResponse:** name, city, location, rating, cost_for_two, price_category, has_online_delivery, cuisines

### 3. Configuration

- CORS: `http://localhost:5173`, `http://localhost:3000`
- Swagger UI: `/docs`

### 4. Testing (Phase 2)

- **`tests/test_backend.py`:** GET /, GET /cities, GET /restaurants (valid/invalid params); mocked DB via dependency override.

---

## Phase 3 — LLM Recommendation Layer (Implemented)

### 1. Structure

```
backend/
├── llm/
│   ├── __init__.py
│   ├── client.py      # Grok API client (httpx, OpenAI-compatible)
│   └── prompts.py     # System/user prompt templates
└── routers/
    └── recommendations.py
```

### 2. Grok Client

- **Config:** `GROK_API_KEY`, `GROK_MODEL`, `GROK_BASE_URL` from env.
- **Design:** Single module for LLM calls; easy to swap provider.
- **Determinism:** `temperature=0`.
- **API:** OpenAI-compatible `POST {base_url}/chat/completions`.

### 3. POST /recommendations

**Request:**
```json
{
  "city": "Bangalore",
  "price_category": "$$",
  "limit": 3
}
```

**Validation:** `limit` 3–10; `price_category` must be $, $$, or $$$.

**Flow:** Query DB (top 20 by rating) → build prompt → call Grok → parse JSON → validate and filter (drop any restaurant not in the provided list) → return up to `limit` recommendations.

**Response:** `{ "recommendations": [ { "rank", "name", "location", "rating", "cost_for_two", "online_order", "reason" }, ... ] }`

### 4. Defensive Checks (Implemented)

- Empty candidate set → 404.
- Missing/invalid `GROK_API_KEY` or LLM error → 503.
- Invalid JSON or missing `recommendations` → 503.
- Any recommendation not in the provided list is dropped (LLM cannot invent restaurants).

### 5. Testing (Phase 3)

- **`tests/test_recommendations.py`:** POST /recommendations (success, 404, 422, 503); LLM client helpers (`_extract_json`, `rank_restaurants` with no key / empty list).

---

## Phase 4 — Frontend (Implemented)

### 1. Stack

- Vite + React, plain CSS or minimal library, no auth.

### 2. Components

| Component | Purpose |
|-----------|---------|
| CityDropdown | Searchable; GET /cities |
| PriceDropdown | $, $$, $$$ |
| ResultCountSelector | 3–10 |
| RecommendButton | POST /recommendations |
| RestaurantCard | Rank, name, location, rating, cost, online order, reason |

### 3. State Handling

- Loading, errors (no results, backend error, LLM failure), API base from `VITE_API_URL`.

### 4. Testing (Phase 4)

- **`src/components/*.test.jsx`**: Unit tests for components.
- **`src/App.test.jsx`**: Integration test for the main flow.
- **Runner**: `vitest`.

---

## Validation & Testing

### Run Tests

```bash
# With pytest
pytest tests/ -v

# Without pytest
# Backend tests
python run_tests.py

# Frontend tests
cd frontend
npm test
```

### Validation Script

```bash
./validate.sh
```

Runs unit tests, checks `.env`/GROK_API_KEY, and does a quick API smoke test.

### Manual API Test

```bash
uvicorn backend.main:app --reload
# Then: GET /, GET /cities, GET /restaurants?city=Bangalore&price_category=$$, POST /recommendations
# Or open http://localhost:8000/docs
```

---

## Final Validation Checklist

- [x] Dataset ingestion runs end-to-end (HuggingFace → SQLite)
- [x] Data auto-loads on first server start when DB is empty
- [x] GET /cities and GET /restaurants return correct filtered results
- [x] POST /recommendations returns ranked list with reasons (with valid GROK_API_KEY)
- [x] LLM temperature=0; only restaurants from provided list returned
- [x] Unit tests for Phase 1–3 (58 tests)
- [ ] Phase 4 UI works without page refresh
- [x] GROK_API_KEY via .env; no hardcoded secrets

---

## Architecture Diagram

```mermaid
flowchart TB
    subgraph frontend [Frontend - React - Phase 4]
        UI[CityDropdown, PriceDropdown, ResultCountSelector]
        Btn[RecommendButton]
        Cards[RestaurantCard List]
    end

    subgraph backend [Backend - FastAPI]
        API[REST API]
        DB[(SQLite / optional PostgreSQL)]
        LLM[Grok Client]
        Ingest[ingest.py]
    end

    subgraph external [External]
        HF[HuggingFace Dataset]
        xAI[xAI Grok API]
    end

    UI -->|GET /cities| API
    Btn -->|POST /recommendations| API
    API -->|Query| DB
    API -->|Rank + Explain| LLM
    LLM -->|Chat Completions| xAI
    HF -->|On first startup or manual script| Ingest
    Ingest -->|Populate| DB
```

---

## Dataset-to-Schema Quick Reference

| HF Column | Target | Notes |
|-----------|--------|--------|
| `name` | name | Trim |
| `listed_in(city)` | city | Normalize; Bengaluru→Bangalore |
| `location` | location | Area/locality |
| `rate` | rating | Parse "4.1/5" → float |
| `approx_cost(for two people)` | cost_for_two | Parse int; first value if "800, 900" |
| `online_order` | has_online_delivery | Yes/No → bool |
| `cuisines` | cuisines | Trim or NULL |
| (entire row) | raw_data | Stored as JSON |

---

## Summary of Implementation Decisions

1. **SQLite default:** No PostgreSQL setup; `data/restaurants.db` created automatically.
2. **Auto-load:** Empty DB on startup triggers ingest from HuggingFace (~1–2 min first time).
3. **`.env` required:** App reads `.env`; copy from `.env.example` and set `GROK_API_KEY`.
4. **Shared ingest:** `backend/ingest.py` used by lifespan and by `scripts/ingest_zomato_data.py`.
5. **JSON column:** SQLAlchemy `JSON` (not PostgreSQL `JSONB`) for SQLite/PostgreSQL compatibility.
6. **Unit tests:** 58 tests for transform, ingest, backend API, recommendations; mocked DB and LLM.
7. **Validation:** `validate.sh` and `run_tests.py` for quick checks.
