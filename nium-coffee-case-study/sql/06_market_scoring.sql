-- 06_market_scoring.sql
-- Rank candidate markets for ACME Baristas at the latest year.
--
-- "Maximize the client base" => weight the size of existing coffee demand most heavily,
-- but reward momentum so we don't recommend large-but-shrinking markets.
--   size_score   : percentile rank of latest-year domestic consumption (the client base today)
--   growth_score : percentile rank of 5-year CAGR (momentum / trajectory)
--   composite    : 0.60*size + 0.40*growth
-- per_capita_kg is carried for context (maturity vs head-room discussion), not scored,
-- so we don't penalise huge markets that simply have large populations.
--
-- Candidate filter: must have positive consumption AND population at the latest year
-- (a real, measurable market).

DROP TABLE IF EXISTS analytics.market_score CASCADE;

CREATE TABLE analytics.market_score AS
WITH latest AS (
    SELECT *
    FROM analytics.consumption_per_capita
    WHERE is_latest_year
      AND domestic_consumption_kg > 0
      AND population > 0
),
scored AS (
    SELECT
        l.country_id,
        l.country_name,
        l.iso2,
        l.iso3,
        l.lat,
        l.lon,
        l.year,
        l.domestic_consumption_kg,
        l.population,
        l.per_capita_kg,
        l.production_kg,
        l.imports_kg,
        l.exports_kg,
        mg.yoy_pct,
        mg.cagr_5y_pct,
        mg.cagr_10y_pct,
        PERCENT_RANK() OVER (ORDER BY l.domestic_consumption_kg)        AS size_score,
        PERCENT_RANK() OVER (ORDER BY COALESCE(mg.cagr_5y_pct, -999))   AS growth_score
    FROM latest l
    LEFT JOIN analytics.market_growth mg
      ON l.country_id = mg.country_id
)
SELECT
    s.*,
    ROUND((0.60 * s.size_score + 0.40 * s.growth_score)::numeric, 4) AS composite_score,
    -- Net trade position: a quick supply-risk signal. Net importers depend on
    -- external supply (price/availability risk); net producers are insulated.
    CASE
        WHEN s.production_kg >= COALESCE(s.imports_kg, 0) THEN 'Net producer'
        ELSE 'Net importer'
    END AS supply_position,
    DENSE_RANK() OVER (
        ORDER BY (0.60 * s.size_score + 0.40 * s.growth_score) DESC
    ) AS market_rank
FROM scored s
ORDER BY market_rank;
