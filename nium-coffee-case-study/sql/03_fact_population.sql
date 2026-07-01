-- 03_fact_population.sql
-- Population fact: one row per (country, year). World Bank rows are keyed by ISO3
-- and joined directly to dim_country. Aggregate rows (regions, income groups, "World")
-- carry non-ISO3 codes absent from dim_country and are therefore excluded.

DROP TABLE IF EXISTS core.fact_population CASCADE;

CREATE TABLE core.fact_population AS
SELECT
    d.country_id,
    p.year,
    p.population
FROM staging.population p
JOIN core.dim_country d
  ON p.iso3 = d.iso3;

ALTER TABLE core.fact_population ADD PRIMARY KEY (country_id, year);
