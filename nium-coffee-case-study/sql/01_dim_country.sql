-- 01_dim_country.sql
-- Canonical country dimension built from the opendatasoft country-codes crosswalk.
-- This is the single source of truth that bridges the two fact sources:
--   coffee (keyed by ISO2)  and  population (keyed by ISO3).
-- Joining both facts THROUGH this table is what discards non-country aggregates
-- (e.g. World Bank "World" / income groups, USDA regional groupings).

DROP TABLE IF EXISTS core.dim_country CASCADE;

CREATE TABLE core.dim_country AS
SELECT
    iso3                         AS country_id,   -- ISO3 is the primary key (population key)
    iso2,
    iso3,
    onu_code,
    country_name,
    lat,
    lon
FROM staging.country_codes
WHERE iso3 IS NOT NULL;

ALTER TABLE core.dim_country ADD PRIMARY KEY (country_id);
CREATE INDEX idx_dim_country_iso2 ON core.dim_country (iso2);
