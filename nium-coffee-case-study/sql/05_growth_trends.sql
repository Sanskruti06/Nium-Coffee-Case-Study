-- 05_growth_trends.sql
-- Two trend outputs:
--   analytics.global_trend   : worldwide coffee consumption by year (+ YoY %) -> "is now a good time?"
--   analytics.market_growth  : per-country momentum (YoY %, 5y & 10y CAGR) at the latest year.

DROP TABLE IF EXISTS analytics.global_trend CASCADE;

CREATE TABLE analytics.global_trend AS
WITH by_year AS (
    SELECT
        year,
        SUM(domestic_consumption_kg) AS world_consumption_kg,
        SUM(population)              AS covered_population
    FROM analytics.consumption_per_capita
    WHERE domestic_consumption_kg IS NOT NULL
    GROUP BY year
)
SELECT
    year,
    world_consumption_kg,
    covered_population,
    world_consumption_kg / NULLIF(covered_population, 0) AS world_per_capita_kg,
    100.0 * (world_consumption_kg - LAG(world_consumption_kg) OVER (ORDER BY year))
          / NULLIF(LAG(world_consumption_kg) OVER (ORDER BY year), 0) AS yoy_pct
FROM by_year
ORDER BY year;


DROP TABLE IF EXISTS analytics.market_growth CASCADE;

CREATE TABLE analytics.market_growth AS
WITH series AS (
    SELECT
        country_id,
        country_name,
        year,
        domestic_consumption_kg,
        per_capita_kg,
        LAG(domestic_consumption_kg, 1)  OVER w AS prev_1y,
        LAG(domestic_consumption_kg, 5)  OVER w AS prev_5y,
        LAG(domestic_consumption_kg, 10) OVER w AS prev_10y
    FROM analytics.consumption_per_capita
    WHERE domestic_consumption_kg IS NOT NULL
    WINDOW w AS (PARTITION BY country_id ORDER BY year)
),
latest AS (
    SELECT MAX(year) AS latest_year FROM series
)
SELECT
    s.country_id,
    s.country_name,
    s.year,
    s.domestic_consumption_kg,
    s.per_capita_kg,
    100.0 * (s.domestic_consumption_kg - s.prev_1y) / NULLIF(s.prev_1y, 0) AS yoy_pct,
    -- CAGR = (end/start)^(1/n) - 1, expressed as a percentage.
    100.0 * (POWER(s.domestic_consumption_kg / NULLIF(s.prev_5y, 0),  1.0/5)  - 1) AS cagr_5y_pct,
    100.0 * (POWER(s.domestic_consumption_kg / NULLIF(s.prev_10y, 0), 1.0/10) - 1) AS cagr_10y_pct
FROM series s
CROSS JOIN latest l
WHERE s.year = l.latest_year;
