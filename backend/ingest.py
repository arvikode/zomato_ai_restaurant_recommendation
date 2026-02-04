"""
Shared ingest logic - loads HuggingFace dataset into DB.
Used by startup (when empty) and scripts/ingest_zomato_data.py.
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.config import get_db_url
from backend.models import Base, Restaurant
from scripts.transform import transform_row

logger = logging.getLogger(__name__)

COL_APPROX_COST = "approx_cost(for two people)"
COL_LISTED_IN_CITY = "listed_in(city)"
COL_NAME = "name"
COL_LOCATION = "location"
COL_RATE = "rate"
COL_ONLINE_ORDER = "online_order"
COL_CUISINES = "cuisines"


def run_ingest(db_url: str | None = None) -> tuple[int, int, int]:
    """
    Load HuggingFace dataset and insert into DB.
    Returns (processed, skipped, inserted).
    """
    from datasets import load_dataset

    url = db_url or get_db_url()
    engine = create_engine(url, connect_args={"check_same_thread": False} if "sqlite" in url else {})

    Base.metadata.create_all(engine)

    # Clear existing data (idempotent)
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM restaurants"))
        conn.commit()

    logger.info("Loading dataset from HuggingFace...")
    dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")

    processed = 0
    skipped = 0
    records = []

    for row in dataset:
        processed += 1
        transformed = transform_row(dict(row))
        if transformed is None:
            skipped += 1
            continue
        raw = transformed.pop("raw_data")
        records.append(Restaurant(**transformed, raw_data=raw))

    if not records:
        logger.warning("No records to insert.")
        return processed, skipped, 0

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    with Session() as session:
        session.add_all(records)
        session.commit()

    logger.info("Rows processed: %d, skipped: %d, inserted: %d", processed, skipped, len(records))
    return processed, skipped, len(records)


def is_db_empty(db_url: str | None = None) -> bool:
    """Check if restaurants table is empty or does not exist."""
    from sqlalchemy import text

    url = db_url or get_db_url()
    engine = create_engine(url, connect_args={"check_same_thread": False} if "sqlite" in url else {})
    Base.metadata.create_all(engine)  # Ensure table exists
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM restaurants"))
            count = result.scalar() or 0
            return count == 0
        except Exception:
            return True
