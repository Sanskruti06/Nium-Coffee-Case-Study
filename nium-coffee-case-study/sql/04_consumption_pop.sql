-- 04_consumption_pop.sql
-- The core analytical join: coffee  +  population  +  country attributes.
-- Produces one tidy row per (country, year) with consumption, population, and the
-- derived per-capita demand metric (kg of coffee per person per year).
-- A latest-year flag marks the most recent year that actually has consumption data,
-- so the dashboard and scoring can snapshot "today" without hard-coding a year.

DROP TABLE IF EXISTS analytics.consumption_per_capita CASCADE;

CREATE TABLE analytics.consumption_per_capita AS
WITH joined AS (
    SELECT
        d.country_id,
        d.country_name,
        d.iso2,
        d.iso3,
        d.lat,
        d.lon,
        fc.year,
        fc.domestic_consumption_kg,
        fc.production_kg,
        fc.imports_kg,
        fc.exports_kg,
        fp.population,
        CASE
            WHEN fp.population > 0 AND fc.domestic_consumption_kg IS NOT NULL
            THEN fc.domestic_consumption_kg / fp.population
        END AS per_capita_kg
    FROM core.fact_coffee fc
    JOIN core.fact_population fp
      ON fc.country_id = fp.country_id AND fc.year = fp.year
    JOIN core.dim_country d
      ON fc.country_id = d.country_id
),
latest AS (
    SELECT MAX(year) AS latest_year
    FROM joined
    WHERE domestic_consumption_kg IS NOT NULL
)
SELECT
    j.*,
    (j.year = l.latest_year) AS is_latest_year
FROM joined j
CROSS JOIN latest l;

CREATE INDEX idx_cpc_country_year ON analytics.consumption_per_capita (country_id, year);
CREATE INDEX idx_cpc_latest ON analytics.consumption_per_capita (is_latest_year);
