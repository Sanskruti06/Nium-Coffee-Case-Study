-- 00_schema.sql
-- Create the three logical layers of the warehouse.
--   staging   : raw-but-clean tables loaded by the pandas pipeline (load_staging.py)
--   core      : conformed dimensional model (dim_country, fact_coffee, fact_population)
--   analytics : business-facing transformation outputs consumed by the dashboard
--
-- staging.* is created by Python (df.to_sql); the other layers are built by the
-- numbered SQL files that follow. We (re)create schemas idempotently here.

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;
