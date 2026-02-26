-- =========================
-- FinOps Multicloud Canonical Model (v0) - PostgreSQL
-- =========================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================
-- Enums
-- =========================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cloud_provider') THEN
    CREATE TYPE cloud_provider AS ENUM ('aws', 'azure', 'oci');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scope_type') THEN
    CREATE TYPE scope_type AS ENUM ('aws_account', 'azure_subscription', 'oci_tenancy', 'oci_compartment', 'unknown');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
    CREATE TYPE job_status AS ENUM ('queued', 'running', 'success', 'failed', 'partial');
  END IF;
END$$;

-- =========================
-- Dimensions
-- =========================

-- Scope = "who pays": AWS account / Azure subscription / OCI compartment/tenancy
CREATE TABLE IF NOT EXISTS dim_scope (
  scope_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud              cloud_provider NOT NULL,
  scope_type         scope_type NOT NULL DEFAULT 'unknown',
  scope_key          TEXT NOT NULL,
  scope_name         TEXT NULL,
  parent_scope_key   TEXT NULL,
  metadata           JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active          BOOLEAN NOT NULL DEFAULT TRUE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (cloud, scope_key)
);

CREATE TABLE IF NOT EXISTS dim_service (
  service_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud              cloud_provider NOT NULL,
  service_key        TEXT NOT NULL,
  service_name       TEXT NOT NULL,
  raw_service        TEXT NULL,
  metadata           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (cloud, service_key)
);

CREATE TABLE IF NOT EXISTS dim_region (
  region_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud              cloud_provider NOT NULL,
  region_key         TEXT NOT NULL,
  region_name        TEXT NULL,
  metadata           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (cloud, region_key)
);

CREATE TABLE IF NOT EXISTS dim_currency_rate (
  rate_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rate_date          DATE NOT NULL,
  from_currency      TEXT NOT NULL,
  to_currency        TEXT NOT NULL,
  rate               NUMERIC(18,8) NOT NULL,
  source             TEXT NULL,
  metadata           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (rate_date, from_currency, to_currency)
);

-- =========================
-- Ingestion tracking
-- =========================

CREATE TABLE IF NOT EXISTS ingest_job (
  job_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud               cloud_provider NOT NULL,
  status              job_status NOT NULL DEFAULT 'queued',
  started_at          TIMESTAMPTZ NULL,
  finished_at         TIMESTAMPTZ NULL,
  source              TEXT NOT NULL,
  source_window_start DATE NULL,
  source_window_end   DATE NULL,
  dataset_version     TEXT NULL,
  stats               JSONB NOT NULL DEFAULT '{}'::jsonb,
  error               TEXT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fact_ingest_audit (
  audit_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id        UUID NOT NULL REFERENCES ingest_job(job_id) ON DELETE CASCADE,
  cloud         cloud_provider NOT NULL,
  fact_table    TEXT NOT NULL DEFAULT 'fact_cost_daily',
  rows_inserted BIGINT NOT NULL DEFAULT 0,
  rows_updated  BIGINT NOT NULL DEFAULT 0,
  rows_deleted  BIGINT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================
-- Fact table (Daily)
-- =========================

CREATE TABLE IF NOT EXISTS fact_cost_daily (
  fact_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cost_date     DATE NOT NULL,
  cloud         cloud_provider NOT NULL,

  scope_id      UUID NULL REFERENCES dim_scope(scope_id),
  service_id    UUID NULL REFERENCES dim_service(service_id),
  region_id     UUID NULL REFERENCES dim_region(region_id),

  scope_key     TEXT NOT NULL,
  service_key   TEXT NOT NULL,
  region_key    TEXT NULL,

  currency      TEXT NOT NULL DEFAULT 'USD',
  amount        NUMERIC(18,6) NOT NULL DEFAULT 0,

  amount_brl    NUMERIC(18,6) NULL,
  fx_rate_used  NUMERIC(18,8) NULL,

  charge_type       TEXT NULL,
  pricing_model     TEXT NULL,
  meter_category    TEXT NULL,
  meter_subcategory TEXT NULL,

  resource_id   TEXT NULL,
  resource_name TEXT NULL,

  tags          JSONB NOT NULL DEFAULT '{}'::jsonb,

  source           TEXT NOT NULL DEFAULT 'unknown',
  source_record_id TEXT NULL,
  raw              JSONB NOT NULL DEFAULT '{}'::jsonb,

  job_id        UUID NULL REFERENCES ingest_job(job_id) ON DELETE SET NULL,

  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()

);

-- =========================
-- Indexes
-- =========================
CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_date
  ON fact_cost_daily (cost_date);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_cloud_date
  ON fact_cost_daily (cloud, cost_date);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_scope_date
  ON fact_cost_daily (cloud, scope_key, cost_date);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_service_date
  ON fact_cost_daily (cloud, service_key, cost_date);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_region_date
  ON fact_cost_daily (cloud, region_key, cost_date);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_tags_gin
  ON fact_cost_daily USING GIN (tags);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_raw_gin
  ON fact_cost_daily USING GIN (raw);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_cost_daily_natural_key
  ON fact_cost_daily (
    cost_date,
    cloud,
    scope_key,
    service_key,
    COALESCE(region_key, ''),
    COALESCE(resource_id, ''),
    currency,
    COALESCE(charge_type, ''),
    COALESCE(pricing_model, '')
  );
