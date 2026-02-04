"""
FastAPI application - Phase 2/3 Backend API.
Run from project root: uvicorn backend.main:app --reload
Uses SQLite by default. Data auto-loads from HuggingFace on first startup.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import cities, restaurants, recommendations

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup: load data from HuggingFace if DB is empty."""
    from backend.ingest import is_db_empty, run_ingest

    if is_db_empty():
        logger.info("Database empty - loading data from HuggingFace (this may take 1-2 min)...")
        try:
            run_ingest()
            logger.info("Data load complete.")
        except Exception as e:
            logger.warning("Auto-ingest failed: %s. Run: python scripts/ingest_zomato_data.py", e)
    yield


app = FastAPI(
    title="AI Restaurant Recommender API",
    description="SQLite by default. Data auto-loads on first startup.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # Next.js default
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cities.router)
app.include_router(restaurants.router)
app.include_router(recommendations.router)


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "docs": "/docs"}
