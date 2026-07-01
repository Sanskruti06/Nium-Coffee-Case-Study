# Coffee Consumption Around the World

This is my submission for the coffee market case study. The task was to take three public datasets 
(USDA coffee figures, World Bank population, and a country-code) reference, join them in PostgreSQL, do
the analysis in SQL, and put the findings in a dashboard. The business question underneath it all: if
ACME Baristas is opening a coffee chain in three countries, which three, and is now even a sensible time
to do it?

Short version of the answer: **China, Vietnam and the UK**, and yes, the timing looks good. The rest of
this file explains how I got there, how to run everything, and what I'd change with more time.

## What's in here

```
pipeline/   Python that cleans the raw files and loads them into Postgres
sql/        the actual transformations, one .sql file per step
dashboard/  a Streamlit app that reads the finished tables
data/        the three raw files, plus a crosswalk I had to build (see below)
dump/        where the pg_dump lands
```

The design idea is simple: Python only cleans and loads. Everything else like the joins, the per-person
maths, the growth rates, the scoring happens in SQL, in numbered files you can read top to bottom.
I did it this way partly because the brief asked for SQL transformation files, but mostly because it's
how I'd actually build this at work. Keeping the logic in SQL means anyone can rerun it, read it, or
change one step without touching Python.

## How to run it

Full step-by-step (Homebrew, Python, Postgres from scratch) is in [INSTALL.md](INSTALL.md). If you
already have Python 3.12 and PostgreSQL, it's just:

```bash
createdb coffee_case_study
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                    # default points at the local db
python pipeline/run_pipeline.py         # cleans data, loads it, runs all the SQL
streamlit run dashboard/app.py          # opens the dashboard
```

`run_pipeline.py` does the whole thing in one go: it reshapes the three CSVs, loads them into `staging`
tables, then runs every file in `sql/` in order. It prints a report of any country codes that didn't
match, and finishes by telling you how many rows ended up in the final scoring table.

To produce the database dump for submission (once the pipeline has run):

```bash
pg_dump --no-owner --no-privileges coffee_case_study > dump/coffee_case_study_dump.sql
```

A reviewer can restore that against an empty database with one command:

```bash
createdb coffee_review && psql coffee_review -f dump/coffee_case_study_dump.sql
```

## The database

Three schemas:

- `staging` — the cleaned CSVs, more or less as-is (`coffee`, `population`, `country_codes`, `coffee_crosswalk`)
- `core` — the tidy model: `dim_country`, `fact_coffee`, `fact_population`
- `analytics` — the tables the dashboard and the business questions actually use: `consumption_per_capita`,
  `global_trend`, `market_growth`, `market_score`, plus a couple of validation tables

Population is the natural anchor because it already uses ISO3 codes. The country code file is the bridge
that ties everything to a single country identity, and joining through it has a nice side effect: World
Bank's aggregate rows ("World", "Arab World", income groups) have no real country code, so they simply
drop out instead of me having to blacklist them by hand.

## What I found

I used USDA's *Domestic Consumption* as the stand-in for the size of the customer base, and 2024 as the
reference year (more on why 2024 below). Volumes are in 60kg bags.

For the recommendation I scored each country on two things: how much coffee it already drinks (market
size) and how fast that's growing (5-year CAGR), weighted 60/40 toward size. Pure size on its own is
misleading here — the biggest markets are the US, Brazil and Japan, but Brazil and Japan are actually
*shrinking* and the US is flat and already crowded. Not where you'd want to plant a brand-new chain.

The top three that come out of the scoring:

| Market | 2024 consumption (M bags) | kg/person | Why |
| --- | ---: | ---: | --- |
| China | 6.1 | 0.26 | Growing fast off a tiny per-person base — enormous headroom in a huge population |
| Vietnam | 4.8 | 2.85 | Big producer now building real domestic demand; young, urbanising |
| United Kingdom | 4.5 | 3.90 | Large, steady, high-spend café culture that's still growing |

On timing: global consumption (excluding the EU aggregate) went from about 103M bags in 2014 to 130M in
2024. So the long trend is up and the most recent year re-accelerated — a reasonable moment to enter.

Opportunities and risks fall out of the same numbers. The opportunity is headroom: China drinks 0.26 kg
a head against 4.6 in the US and 7.4 in Canada, so small habit shifts across a billion-plus people move a
lot of volume. The risks are the usual ones; importer markets are exposed to global bean prices (the
dashboard flags each country as a net producer or importer), the mature markets are saturated, and a few
of the high-growth names (Turkey, Egypt, Russia) carry real macro/FX risk that hits discretionary spend.

## Visualisation Snapshot (Streamlit App)

<img width="1454" height="788" alt="image" src="https://github.com/user-attachments/assets/18322193-59b2-41d7-9bde-8776f91a64a1" />


<img width="2894" height="1476" alt="image" src="https://github.com/user-attachments/assets/baece0ea-0783-40fc-9383-3184a779140d" />


<img width="2894" height="1476" alt="image" src="https://github.com/user-attachments/assets/6aa19883-528c-4e01-b612-7408d205bf3d" />


<img width="2880" height="1240" alt="image" src="https://github.com/user-attachments/assets/79bb3959-9141-4120-9f17-777bb3a39e1e" />



## Reflection

**Key design choices.** The big one was keeping Python thin and doing the real work in SQL, for the
reasons above. The other was treating the country crosswalk as a first-class, hand-maintained artifact
rather than something to gloss over — because the moment I looked closely at the data, the codes were the
whole ballgame.

**The challenge that actually mattered.** USDA's country codes aren't ISO. They're an older FIPS-style
scheme, and some of them collide with ISO in dangerous ways: USDA's `CH` is China, but in ISO `CH` is
Switzerland; USDA's `GB` is Gabon, not the UK; `ES` is El Salvador, not Spain. If I'd joined on the codes
naively, I'd have quietly handed China's entire coffee market to Switzerland and lost Japan, the
Philippines, Korea and Vietnam altogether and the results would have looked perfectly plausible while
being wrong. I fixed it by writing an explicit USDA→ISO3 crosswalk (`data/crosswalk_usda_iso.csv`) with
a note against every tricky code, and by having the pipeline report anything that doesn't match instead
of silently dropping it. The other wrinkles were smaller: the World Bank file is "wide" with four junk
header rows and a trailing empty column, and it mixes real countries with regional aggregates.

**Assumptions.** Domestic consumption is a proxy for the addressable market, not for café spend
specifically. Per-person figures use total population, not adults or city-dwellers, so they understate
how intense actual coffee-drinkers are. I treated the coffee marketing year as close enough to a calendar
year for trends. And I picked 2024 as the reference year on purpose: the coffee data runs to 2025 but
World Bank population stops at 2024, and the 2025 coffee file is only partly reported, so 2024 is the last
year where I have both numbers for everyone. I also left the EU out of the country ranking — USDA reports
it as one bloc, not as member states, so it can't fairly sit in a list of individual countries.

**What I'd do with more time.** Bring in income and price data. Layer in something on cafe or competitor density to make it about *where within* a market you'd open, not just which market. Find a second source for EU member-level consumption so the biggest bloc isn't a blind spot. 

**Data that would have helped.** Out-of-home versus at-home consumption, retail coffee prices,
disposable income, urbanisation rates, tourism, and existing chain footprints per capita. Any of those
would turn "big and growing" into a sharper "big, growing, and worth the rent."

---
