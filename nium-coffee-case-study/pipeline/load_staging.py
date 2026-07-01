
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

try:
    from .db import get_engine
    from .extract_transform import main as transform_main
except ImportError:  # allow running as a plain script
    from db import get_engine
    from extract_transform import main as transform_main

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = PROJECT_ROOT / "data" / "processed"


def _load_frames() -> dict[str, pd.DataFrame]:
    files = {
        "coffee": PROCESSED / "coffee.parquet",
        "population": PROCESSED / "population.parquet",
        "country_codes": PROCESSED / "country_codes.parquet",
        "coffee_crosswalk": PROCESSED / "crosswalk.parquet",
    }
    if all(p.exists() for p in files.values()):
        print("Loading cached parquet from data/processed/ ...")
        return {k: pd.read_parquet(v) for k, v in files.items()}
    print("Parquet not found; running transform step ...")
    return transform_main()


def main() -> None:
    frames = _load_frames()
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))

    for name, df in frames.items():
        print(f"Loading staging.{name} ({len(df):,} rows) ...")
        df.to_sql(
            name,
            engine,
            schema="staging",
            if_exists="replace",
            index=False,
            chunksize=10_000,
            method="multi",
        )
    print("Staging load complete.")


if __name__ == "__main__":
    main()
