-- 02_fact_coffee.sql
-- Coffee fact: one row per (country, year) with the kept USDA attributes pivoted
-- into columns. Source values are already converted to kilograms in the pipeline.
--
-- USDA country codes are FIPS-style, NOT ISO. We resolve them to ISO3 through the
-- curated crosswalk (staging.coffee_crosswalk), then to the canonical country via
-- dim_country. Codes with no ISO3 (the 'European Union' aggregate) and codes whose
-- ISO3 is absent from dim_country are dropped here and reported in 99_validation.sql.

DROP TABLE IF EXISTS core.fact_coffee CASCADE;

CREATE TABLE core.fact_coffee AS
SELECT
    d.country_id,
    c.year,
    SUM(c.value_kg) FILTER (WHERE c.attribute = 'Domestic Consumption') AS domestic_consumption_kg,
    SUM(c.value_kg) FILTER (WHERE c.attribute = 'Production')           AS production_kg,
    SUM(c.value_kg) FILTER (WHERE c.attribute = 'Imports')             AS imports_kg,
    SUM(c.value_kg) FILTER (WHERE c.attribute = 'Exports')             AS exports_kg
FROM staging.coffee c
JOIN staging.coffee_crosswalk x
  ON c.usda_code = x.usda_code
JOIN core.dim_country d
  ON x.iso3 = d.iso3
GROUP BY d.country_id, c.year;

ALTER TABLE core.fact_coffee ADD PRIMARY KEY (country_id, year);
