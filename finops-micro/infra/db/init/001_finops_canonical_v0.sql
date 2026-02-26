CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS dim_scope (
  scope_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud VARCHAR(16) NOT NULL,
  scope_key VARCHAR(128) NOT NULL,
  scope_name VARCHAR(256) NOT NULL,
  metadata_json JSONB,
  CONSTRAINT uq_dim_scope_cloud_scope_key UNIQUE (cloud, scope_key)
);

CREATE INDEX IF NOT EXISTS ix_dim_scope_cloud ON dim_scope (cloud);

CREATE TABLE IF NOT EXISTS dim_service (
  service_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud VARCHAR(16) NOT NULL,
  service_key VARCHAR(128) NOT NULL,
  service_name VARCHAR(256) NOT NULL,
  metadata_json JSONB,
  CONSTRAINT uq_dim_service_cloud_service_key UNIQUE (cloud, service_key)
);

CREATE INDEX IF NOT EXISTS ix_dim_service_cloud ON dim_service (cloud);

CREATE TABLE IF NOT EXISTS dim_region (
  region_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud VARCHAR(16) NOT NULL,
  region_key VARCHAR(128) NOT NULL,
  region_name VARCHAR(256) NOT NULL,
  metadata_json JSONB,
  CONSTRAINT uq_dim_region_cloud_region_key UNIQUE (cloud, region_key)
);

CREATE INDEX IF NOT EXISTS ix_dim_region_cloud ON dim_region (cloud);

CREATE TABLE IF NOT EXISTS dim_currency_rate (
  rate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rate_date DATE NOT NULL,
  from_currency VARCHAR(8) NOT NULL,
  to_currency VARCHAR(8) NOT NULL,
  rate NUMERIC(18, 8) NOT NULL,
  CONSTRAINT uq_dim_currency_rate_key UNIQUE (rate_date, from_currency, to_currency)
);

CREATE INDEX IF NOT EXISTS ix_dim_currency_rate_rate_date ON dim_currency_rate (rate_date);

CREATE TABLE IF NOT EXISTS ingest_job (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider VARCHAR(16) NOT NULL,
  status VARCHAR(32) NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  details_json JSONB,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS ix_ingest_job_provider ON ingest_job (provider);
CREATE INDEX IF NOT EXISTS ix_ingest_job_status ON ingest_job (status);

CREATE TABLE IF NOT EXISTS fact_cost_daily (
  fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usage_date DATE NOT NULL,
  cloud VARCHAR(16) NOT NULL,
  scope_id UUID NOT NULL REFERENCES dim_scope(scope_id),
  service_id UUID NOT NULL REFERENCES dim_service(service_id),
  region_id UUID REFERENCES dim_region(region_id),
  currency_code VARCHAR(8) NOT NULL,
  amount NUMERIC(18, 6) NOT NULL,
  amount_brl NUMERIC(18, 6),
  source_ref VARCHAR(128),
  metadata_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_fact_cost_daily_key UNIQUE (
    usage_date,
    cloud,
    scope_id,
    service_id,
    region_id,
    currency_code,
    source_ref
  )
);

CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_usage_date ON fact_cost_daily (usage_date);
CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_cloud ON fact_cost_daily (cloud);
CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_usage_date_cloud ON fact_cost_daily (usage_date, cloud);
