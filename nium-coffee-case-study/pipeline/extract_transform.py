#Step 1 — Extract & transform the three raw sources with pandas.

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"

# Coffee volumes are reported in "1000 60 KG BAGS". One bag = 60 kg.
KG_PER_BAG = 60
BAGS_PER_UNIT = 1000  # values are in thousands of bags


COFFEE_ATTRIBUTES = [
    "Domestic Consumption",
    "Production",
    "Imports",
    "Exports",
]


def transform_coffee() -> pd.DataFrame:
    
    df = pd.read_csv(RAW / "psd_coffee.csv", dtype={"Country_Code": str})
    df = df[df["Attribute_Description"].isin(COFFEE_ATTRIBUTES)].copy()

    df["year"] = pd.to_numeric(df["Market_Year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["Value"], errors="coerce")

    # Convert 1000 60kg bags ->  plain kilograms
    df["value_kg"] = df["value"] * BAGS_PER_UNIT * KG_PER_BAG

    out = df.rename(
        columns={
            "Country_Code": "usda_code",
            "Country_Name": "usda_name",
            "Attribute_Description": "attribute",
        }
    )[["usda_code", "usda_name", "year", "attribute", "value", "value_kg"]]

    out = out.dropna(subset=["usda_code", "year"]).reset_index(drop=True)
    out["year"] = out["year"].astype("int64")
    out["usda_code"] = out["usda_code"].str.strip().str.upper()
    return out


def transform_crosswalk() -> pd.DataFrame:

    df = pd.read_csv(RAW.parent / "crosswalk_usda_iso.csv", dtype=str)
    df["usda_code"] = df["usda_code"].str.strip().str.upper()
    df["iso3"] = df["iso3"].astype("string").str.strip().str.upper()
    return df[["usda_code", "usda_name", "iso3", "note"]]


def transform_population() -> pd.DataFrame:

    #The CSV has 4 metadata rows before the header and a trailing empty column.

    df = pd.read_csv(RAW / "worldbank_population.csv", skiprows=4)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]  # drop trailing empty col

    year_cols = [c for c in df.columns if c.isdigit()]
    long = df.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=year_cols,
        var_name="year",
        value_name="population",
    ).rename(columns={"Country Name": "country_name_src", "Country Code": "iso3"})

    long["year"] = long["year"].astype(int)
    long["population"] = pd.to_numeric(long["population"], errors="coerce")
    long = long.dropna(subset=["population"]).reset_index(drop=True)
    long["population"] = long["population"].astype("int64")
    long["iso3"] = long["iso3"].str.strip().str.upper()
    return long[["iso3", "country_name_src", "year", "population"]]


def transform_country_codes() -> pd.DataFrame:

    df = pd.read_csv(
        RAW / "countries-codes.csv",
        sep=";",
        usecols=["ISO2 CODE", "ISO3 CODE", "ONU CODE", "LABEL EN", "geo_point_2d"],
    )
    df = df.rename(
        columns={
            "ISO2 CODE": "iso2",
            "ISO3 CODE": "iso3",
            "ONU CODE": "onu_code",
            "LABEL EN": "country_name",
        }
    )

    coords = df["geo_point_2d"].str.split(",", expand=True)
    df["lat"] = pd.to_numeric(coords[0], errors="coerce")
    df["lon"] = pd.to_numeric(coords[1], errors="coerce")
    df = df.drop(columns=["geo_point_2d"])

    for col in ("iso2", "iso3"):
        df[col] = df[col].astype("string").str.strip().str.upper()

    # Remove rows with no ISO3 and remove duplicate countries, keeping the first occurrence of each ISO3.
    df = df.dropna(subset=["iso3"])
    df = df.drop_duplicates(subset=["iso3"]).reset_index(drop=True)
    return df[["iso2", "iso3", "onu_code", "country_name", "lat", "lon"]]


def report_unmatched(coffee, pop, dim, xwalk) -> None:
    """Print which source codes fail to join through the crosswalk/bridge (transparency)."""
    # Normalize the crosswalk's nullable-string iso3 to plain str ('' for NA/blank).
    mapped = {
        str(code): ("" if pd.isna(iso3) else str(iso3).strip())
        for code, iso3 in zip(xwalk["usda_code"], xwalk["iso3"])
    }
    coffee_codes = set(coffee["usda_code"])
    no_iso3 = sorted(c for c in coffee_codes if not mapped.get(c))
    dim_iso3 = set(dim["iso3"].dropna())
    iso3_no_country = sorted(
        {mapped[c] for c in coffee_codes if mapped.get(c)} - dim_iso3
    )
    pop_unmatched = sorted(set(pop["iso3"]) - dim_iso3)
    print(f"  Coffee codes with no ISO3 (aggregates/excluded) ({len(no_iso3)}): {no_iso3}")
    print(f"  Coffee ISO3 not found in country dim ({len(iso3_no_country)}): {iso3_no_country}")
    print(f"  Population ISO3 not found in country dim ({len(pop_unmatched)}): "
          f"{pop_unmatched[:25]}{' ...' if len(pop_unmatched) > 25 else ''}")


def main() -> dict[str, pd.DataFrame]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("Transforming coffee ...")
    coffee = transform_coffee()
    print(f"  -> {len(coffee):,} rows")
    print("Transforming population ...")
    pop = transform_population()
    print(f"  -> {len(pop):,} rows")
    print("Transforming country codes ...")
    dim = transform_country_codes()
    print(f"  -> {len(dim):,} rows")
    print("Loading USDA->ISO3 crosswalk ...")
    xwalk = transform_crosswalk()
    print(f"  -> {len(xwalk):,} rows")

    print("Unmatched-code report:")
    report_unmatched(coffee, pop, dim, xwalk)

    coffee.to_parquet(PROCESSED / "coffee.parquet", index=False)
    pop.to_parquet(PROCESSED / "population.parquet", index=False)
    dim.to_parquet(PROCESSED / "country_codes.parquet", index=False)
    xwalk.to_parquet(PROCESSED / "crosswalk.parquet", index=False)
    print(f"Wrote parquet files to {PROCESSED}")

    return {"coffee": coffee, "population": pop, "country_codes": dim, "coffee_crosswalk": xwalk}


if __name__ == "__main__":
    main()
