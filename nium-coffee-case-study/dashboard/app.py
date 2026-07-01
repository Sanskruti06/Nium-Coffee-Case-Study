"""ACME Baristas — Global Coffee Market Dashboard (Streamlit + Plotly).

Reads the analytics.* tables produced by the SQL transformation layer and presents:
  - headline KPIs
  - global consumption trend  ("is now a good time to enter?")
  - choropleth map of consumption / per-capita demand
  - the top-3 recommended markets with scoring rationale
  - a per-country drill-down (consumption vs production = supply-risk view)

Run:  streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Make pipeline.db importable when running from the project root.
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pipeline.db import get_engine  # noqa: E402

st.set_page_config(page_title="ACME Baristas — Coffee Markets", page_icon="☕", layout="wide")


@st.cache_resource
def _engine():
    return get_engine()


@st.cache_data(ttl=600)
def load(table: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM analytics.{table}", _engine())


def kg_to_bags_m(kg: float) -> float:
    """kg -> millions of 60kg bags (the unit coffee people think in)."""
    return kg / 60 / 1_000_000


# ---------------------------------------------------------------- load data
try:
    cpc = load("consumption_per_capita")
    trend = load("global_trend")
    score = load("market_score")        
    val = load("validation_report")
except Exception as exc:  # noqa: BLE001
    st.error(
        "Could not read analytics tables. Run the pipeline first:\n\n"
        "    python pipeline/run_pipeline.py\n\n"
        f"Details: {exc}"
    )
    st.stop()

latest_year = int(cpc.loc[cpc["is_latest_year"], "year"].max())

st.title("☕ ACME Baristas — Global Coffee Market Analysis")

# ---------------------------------------------------------------- KPIs
latest_trend = trend.sort_values("year").iloc[-1]
top_market = score.sort_values("market_rank").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("World consumption (latest)", f"{kg_to_bags_m(latest_trend.world_consumption_kg):,.1f} M bags")
c2.metric("World YoY growth", f"{latest_trend.yoy_pct:+.1f}%")
c3.metric("Top recommended market", str(top_market.country_name))

st.divider()

# ---------------------------------------------------------------- global trend
left, right = st.columns([3, 2])
with left:
    st.subheader("Global coffee consumption over time")
    fig = px.area(
        trend, x="year", y="world_consumption_kg",
        labels={"world_consumption_kg": "Consumption (kg)", "year": "Year"},
    )
    fig.update_layout(margin=dict(t=10, b=10), height=360)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("A sustained upward trend signals a growing addressable market — favourable timing for entry.")
with right:
    st.subheader("Year-over-year growth (%)")
    fig = px.bar(trend.dropna(subset=["yoy_pct"]), x="year", y="yoy_pct",
                 labels={"yoy_pct": "YoY %", "year": "Year"})
    fig.update_layout(margin=dict(t=10, b=10), height=360)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------- map
st.subheader(f"Coffee demand by country ({latest_year})")
metric = st.radio(
    "Map metric", ["Total consumption", "Per-capita consumption"],
    horizontal=True, label_visibility="collapsed",
)
latest = cpc[cpc["is_latest_year"]].copy()
if metric == "Total consumption":
    color_col, color_label = "domestic_consumption_kg", "Consumption (kg)"
else:
    color_col, color_label = "per_capita_kg", "kg / person"
fig = px.choropleth(
    latest, locations="iso3", color=color_col, hover_name="country_name",
    color_continuous_scale="YlOrBr", labels={color_col: color_label},
)
fig.update_layout(margin=dict(t=10, b=10), height=420,
                  coloraxis_colorbar=dict(title=color_label))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------- top 3 recommendation
st.subheader("🏆 Recommended markets for ACME Baristas")


top = score.sort_values("market_rank").head(15).copy()
top["consumption_M_bags"] = top["domestic_consumption_kg"].apply(kg_to_bags_m)

podium = top.head(3)
pcols = st.columns(3)
medals = ["🥇", "🥈", "🥉"]
for col, medal, (_, row) in zip(pcols, medals, podium.iterrows()):
    col.markdown(f"### {medal} {row.country_name}")
    col.metric("Consumption", f"{row.consumption_M_bags:,.1f} M bags")
    col.caption(f"Supply: {row.supply_position}  ·  composite {row.composite_score:.3f}")

st.markdown("##### Full ranking (top 15)")
show = top[[
    "market_rank", "country_name", "consumption_M_bags", "supply_position",
]].rename(columns={
    "market_rank": "Rank", "country_name": "Market",
    "consumption_M_bags": "Consumption (M bags)", "supply_position": "Supply",
})
st.dataframe(show, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------- drill-down
st.subheader("Country drill-down — demand vs domestic supply")
countries = sorted(cpc["country_name"].dropna().unique())
default = str(top_market.country_name)
sel = st.selectbox("Country", countries, index=countries.index(default) if default in countries else 0)
hist = cpc[cpc["country_name"] == sel].sort_values("year")
long = hist.melt(
    id_vars="year",
    value_vars=["domestic_consumption_kg", "production_kg", "imports_kg"],
    var_name="metric", value_name="kg",
).dropna(subset=["kg"])
long["metric"] = long["metric"].map({
    "domestic_consumption_kg": "Consumption",
    "production_kg": "Production",
    "imports_kg": "Imports",
})
fig = px.line(long, x="year", y="kg", color="metric",
              labels={"kg": "kg", "year": "Year", "metric": ""})
fig.update_layout(height=380, margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

