"""
Backend configuration from environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def get_db_url() -> str:
    """
    Build database URL. Defaults to SQLite (no setup required).
    Set DATABASE_URL for PostgreSQL: postgresql://user:pass@host:port/db
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # Default: SQLite file in project data/ folder
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    return f"sqlite:///{data_dir / 'restaurants.db'}"
