"""Database connection helper.

Reads DATABASE_URL from the environment (.env file) and exposes a single
SQLAlchemy engine used by every pipeline step and the dashboard.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# Load .env from the project root (one level above this file's pipeline/ dir).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_URL = "postgresql+psycopg2://localhost:5432/coffee_case_study"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)


def get_engine() -> Engine:
    """Return a SQLAlchemy engine for the configured PostgreSQL database."""
    return create_engine(DATABASE_URL, future=True)


if __name__ == "__main__":
    # Quick connectivity check: `python pipeline/db.py`
    from sqlalchemy import text

    eng = get_engine()
    with eng.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar_one()
    print("Connected OK ->", version)
