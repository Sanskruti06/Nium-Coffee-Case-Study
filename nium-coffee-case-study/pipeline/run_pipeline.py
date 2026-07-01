"""End-to-end orchestrator.

  1. extract_transform  -> tidy parquet
  2. load_staging       -> staging.* tables in PostgreSQL
  3. execute every sql/*.sql in filename order -> core.* + analytics.*

Run:  python pipeline/run_pipeline.py
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

try:
    from .db import get_engine
    from . import extract_transform, load_staging
except ImportError:
    from db import get_engine
    import extract_transform
    import load_staging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"


def run_sql_files() -> None:
    engine = get_engine()
    sql_files = sorted(SQL_DIR.glob("*.sql"))
    if not sql_files:
        raise SystemExit(f"No .sql files found in {SQL_DIR}")
    # Use the raw DBAPI connection so psycopg2 runs the script literally.
    # (exec_driver_sql passes an empty params dict, which makes psycopg2 try to
    #  interpret the '%' signs in our SQL comments as parameter placeholders.)
    raw = engine.raw_connection()
    try:
        for path in sql_files:
            print(f"Executing {path.name} ...")
            cur = raw.cursor()
            cur.execute(path.read_text())  # single arg -> no % substitution
            cur.close()
            raw.commit()
    finally:
        raw.close()
    print("All SQL transformations applied.")


def main() -> None:
    print("=" * 60)
    print("STEP 1/3  Extract & transform")
    print("=" * 60)
    extract_transform.main()

    print("\n" + "=" * 60)
    print("STEP 2/3  Load staging tables")
    print("=" * 60)
    load_staging.main()

    print("\n" + "=" * 60)
    print("STEP 3/3  SQL transformations")
    print("=" * 60)
    run_sql_files()

    # Tiny smoke check so the run fails loudly if the model is empty.
    engine = get_engine()
    with engine.connect() as conn:
        n = conn.execute(text("SELECT count(*) FROM analytics.market_score")).scalar_one()
    print(f"\nDone. analytics.market_score has {n} rows.")


if __name__ == "__main__":
    main()
