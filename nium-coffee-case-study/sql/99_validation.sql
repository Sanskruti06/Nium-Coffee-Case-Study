-- 99_validation.sql
-- QA + transparency. Builds analytics.validation_report (one row per check) and
-- analytics.unmatched_codes (source codes that failed to join the country bridge).
-- These back the data-quality notes in the README. Nothing here changes the model.

DROP TABLE IF EXISTS analytics.unmatched_codes CASCADE;

CREATE TABLE analytics.unmatched_codes AS
-- Coffee USDA codes that resolve to no country: either no ISO3 in the crosswalk
-- (e.g. the 'European Union' aggregate) or an ISO3 absent from dim_country.
SELECT DISTINCT
    'coffee' AS source,
    c.usda_code AS code,
    c.usda_name AS source_name
FROM staging.coffee c
LEFT JOIN staging.coffee_crosswalk x ON c.usda_code = x.usda_code
LEFT JOIN core.dim_country d ON x.iso3 = d.iso3
WHERE d.country_id IS NULL
UNION ALL
-- Population ISO3 codes with no country match (World Bank aggregates / income groups).
SELECT DISTINCT
    'population' AS source,
    p.iso3       AS code,
    p.country_name_src AS source_name
FROM staging.population p
LEFT JOIN core.dim_country d ON p.iso3 = d.iso3
WHERE d.iso3 IS NULL;


DROP TABLE IF EXISTS analytics.validation_report CASCADE;

CREATE TABLE analytics.validation_report AS
SELECT 'staging.coffee rows'              AS check_name, COUNT(*)::text AS value FROM staging.coffee
UNION ALL SELECT 'staging.population rows',        COUNT(*)::text FROM staging.population
UNION ALL SELECT 'staging.country_codes rows',     COUNT(*)::text FROM staging.country_codes
UNION ALL SELECT 'staging.coffee_crosswalk rows',  COUNT(*)::text FROM staging.coffee_crosswalk
UNION ALL SELECT 'core.dim_country rows',          COUNT(*)::text FROM core.dim_country
UNION ALL SELECT 'core.fact_coffee rows',          COUNT(*)::text FROM core.fact_coffee
UNION ALL SELECT 'core.fact_population rows',       COUNT(*)::text FROM core.fact_population
UNION ALL SELECT 'analytics.consumption_per_capita rows', COUNT(*)::text FROM analytics.consumption_per_capita
UNION ALL SELECT 'analytics.market_score rows',     COUNT(*)::text FROM analytics.market_score
UNION ALL SELECT 'latest data year',                MAX(year)::text FROM analytics.consumption_per_capita WHERE is_latest_year
UNION ALL SELECT 'unmatched coffee codes',          COUNT(*)::text FROM analytics.unmatched_codes WHERE source='coffee'
UNION ALL SELECT 'unmatched population codes',      COUNT(*)::text FROM analytics.unmatched_codes WHERE source='population';
