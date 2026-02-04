#!/usr/bin/env python3
"""
Phase 1: Ingest Zomato restaurant data from HuggingFace into DB.
Idempotent: clears table before insert.
Run from repo root: python scripts/ingest_zomato_data.py
Uses SQLite by default (no PostgreSQL required).
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from backend.ingest import run_ingest

if __name__ == "__main__":
    run_ingest()
