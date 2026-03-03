BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.dim_tenant (
  tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cloud public.cloud_provider NOT NULL,
  tenant_key TEXT NOT NULL,
  tenant_name TEXT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_dim_tenant_cloud_tenant_key UNIQUE (cloud, tenant_key)
);

CREATE INDEX IF NOT EXISTS ix_dim_tenant_cloud
  ON public.dim_tenant (cloud);

ALTER TABLE public.dim_scope
  ADD COLUMN IF NOT EXISTS tenant_id UUID NULL;

ALTER TABLE public.fact_cost_daily
  ADD COLUMN IF NOT EXISTS tenant_id UUID NULL;

ALTER TABLE public.ingest_job
  ADD COLUMN IF NOT EXISTS tenant_id UUID NULL;

ALTER TABLE public.fact_ingest_audit
  ADD COLUMN IF NOT EXISTS tenant_id UUID NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_dim_scope_tenant_id_dim_tenant'
  ) THEN
    ALTER TABLE public.dim_scope
      ADD CONSTRAINT fk_dim_scope_tenant_id_dim_tenant
      FOREIGN KEY (tenant_id) REFERENCES public.dim_tenant(tenant_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_fact_cost_daily_tenant_id_dim_tenant'
  ) THEN
    ALTER TABLE public.fact_cost_daily
      ADD CONSTRAINT fk_fact_cost_daily_tenant_id_dim_tenant
      FOREIGN KEY (tenant_id) REFERENCES public.dim_tenant(tenant_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_ingest_job_tenant_id_dim_tenant'
  ) THEN
    ALTER TABLE public.ingest_job
      ADD CONSTRAINT fk_ingest_job_tenant_id_dim_tenant
      FOREIGN KEY (tenant_id) REFERENCES public.dim_tenant(tenant_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_fact_ingest_audit_tenant_id_dim_tenant'
  ) THEN
    ALTER TABLE public.fact_ingest_audit
      ADD CONSTRAINT fk_fact_ingest_audit_tenant_id_dim_tenant
      FOREIGN KEY (tenant_id) REFERENCES public.dim_tenant(tenant_id);
  END IF;
END$$;

INSERT INTO public.dim_tenant (cloud, tenant_key, tenant_name, metadata)
SELECT ds.cloud, ds.scope_key, NULLIF(ds.scope_name, ''), jsonb_build_object('backfill', true, 'source', 'scope_root')
FROM public.dim_scope ds
WHERE ds.scope_type IN ('oci_tenancy', 'azure_subscription', 'aws_account')
ON CONFLICT (cloud, tenant_key) DO UPDATE
SET tenant_name = COALESCE(EXCLUDED.tenant_name, public.dim_tenant.tenant_name),
    metadata = public.dim_tenant.metadata || EXCLUDED.metadata,
    updated_at = now();

INSERT INTO public.dim_tenant (cloud, tenant_key, tenant_name, metadata)
SELECT DISTINCT base.cloud, 'default', initcap(base.cloud::text) || ' Default', jsonb_build_object('backfill', true, 'source', 'default')
FROM (
  SELECT cloud FROM public.dim_scope
  UNION
  SELECT cloud FROM public.fact_cost_daily
  UNION
  SELECT cloud FROM public.ingest_job
  UNION
  SELECT cloud FROM public.fact_ingest_audit
) AS base
ON CONFLICT (cloud, tenant_key) DO NOTHING;

UPDATE public.dim_scope AS ds
SET tenant_id = dt.tenant_id
FROM public.dim_tenant AS dt
WHERE ds.tenant_id IS NULL
  AND ds.cloud = dt.cloud
  AND ds.scope_key = dt.tenant_key;

UPDATE public.dim_scope AS ds
SET tenant_id = dt.tenant_id
FROM public.dim_scope AS root_scope
JOIN public.dim_tenant AS dt
  ON dt.cloud = root_scope.cloud
 AND dt.tenant_key = root_scope.scope_key
WHERE ds.tenant_id IS NULL
  AND ds.parent_scope_key IS NOT NULL
  AND root_scope.cloud = ds.cloud
  AND root_scope.scope_key = ds.parent_scope_key
  AND root_scope.scope_type IN ('oci_tenancy', 'azure_subscription', 'aws_account');

UPDATE public.dim_scope AS ds
SET tenant_id = dt.tenant_id
FROM public.dim_tenant AS dt
WHERE ds.tenant_id IS NULL
  AND dt.cloud = ds.cloud
  AND dt.tenant_key = 'default';

INSERT INTO public.dim_scope (
  tenant_id,
  cloud,
  scope_type,
  scope_key,
  scope_name,
  metadata,
  is_active,
  created_at,
  updated_at
)
SELECT dt.tenant_id, facts.cloud, 'unknown', facts.scope_key, facts.scope_key,
       jsonb_build_object('backfill', true, 'source', 'fact_cost_daily'),
       TRUE, now(), now()
FROM (
  SELECT DISTINCT cloud, scope_key
  FROM public.fact_cost_daily
  WHERE scope_key IS NOT NULL
) AS facts
JOIN public.dim_tenant AS dt
  ON dt.cloud = facts.cloud
 AND dt.tenant_key = 'default'
LEFT JOIN public.dim_scope AS ds
  ON ds.tenant_id = dt.tenant_id
 AND ds.scope_key = facts.scope_key
WHERE ds.scope_id IS NULL;

UPDATE public.fact_cost_daily AS f
SET tenant_id = ds.tenant_id
FROM public.dim_scope AS ds
WHERE f.tenant_id IS NULL
  AND f.scope_id IS NOT NULL
  AND ds.scope_id = f.scope_id;

UPDATE public.fact_cost_daily AS f
SET tenant_id = dt.tenant_id
FROM public.dim_tenant AS dt
WHERE f.tenant_id IS NULL
  AND dt.cloud = f.cloud
  AND dt.tenant_key = 'default';

UPDATE public.fact_cost_daily AS f
SET scope_id = ds.scope_id
FROM public.dim_scope AS ds
WHERE f.scope_id IS NULL
  AND f.tenant_id IS NOT NULL
  AND ds.tenant_id = f.tenant_id
  AND ds.scope_key = f.scope_key;

UPDATE public.fact_cost_daily AS f
SET scope_id = ds.scope_id
FROM public.dim_scope AS ds
JOIN public.dim_tenant AS dt
  ON dt.tenant_id = ds.tenant_id
WHERE f.scope_id IS NULL
  AND dt.cloud = f.cloud
  AND dt.tenant_key = 'default'
  AND ds.scope_key = f.scope_key;

UPDATE public.ingest_job AS job
SET tenant_id = dt.tenant_id
FROM public.dim_tenant AS dt
WHERE job.tenant_id IS NULL
  AND dt.cloud = job.cloud
  AND dt.tenant_key = 'default';

UPDATE public.fact_ingest_audit AS audit
SET tenant_id = job.tenant_id
FROM public.ingest_job AS job
WHERE audit.tenant_id IS NULL
  AND job.job_id = audit.job_id;

UPDATE public.fact_ingest_audit AS audit
SET tenant_id = dt.tenant_id
FROM public.dim_tenant AS dt
WHERE audit.tenant_id IS NULL
  AND dt.cloud = audit.cloud
  AND dt.tenant_key = 'default';

DO $$
DECLARE
  old_constraint_name TEXT;
BEGIN
  SELECT conname
  INTO old_constraint_name
  FROM pg_constraint
  WHERE conrelid = 'public.dim_scope'::regclass
    AND contype = 'u'
    AND pg_get_constraintdef(oid) LIKE '%(cloud, scope_key)%'
  LIMIT 1;

  IF old_constraint_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE public.dim_scope DROP CONSTRAINT %I', old_constraint_name);
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.dim_scope'::regclass
      AND conname = 'uq_dim_scope_tenant_scope_key'
  ) THEN
    ALTER TABLE public.dim_scope
      ADD CONSTRAINT uq_dim_scope_tenant_scope_key UNIQUE (tenant_id, scope_key);
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.dim_scope WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Backfill falhou: dim_scope.tenant_id ainda contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.fact_cost_daily WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Backfill falhou: fact_cost_daily.tenant_id ainda contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.fact_cost_daily WHERE scope_id IS NULL) THEN
    RAISE EXCEPTION 'Backfill falhou: fact_cost_daily.scope_id ainda contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.ingest_job WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Backfill falhou: ingest_job.tenant_id ainda contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.fact_ingest_audit WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Backfill falhou: fact_ingest_audit.tenant_id ainda contem NULL';
  END IF;
END$$;

ALTER TABLE public.dim_scope
  ALTER COLUMN tenant_id SET NOT NULL;

ALTER TABLE public.fact_cost_daily
  ALTER COLUMN tenant_id SET NOT NULL;

ALTER TABLE public.fact_cost_daily
  ALTER COLUMN scope_id SET NOT NULL;

ALTER TABLE public.ingest_job
  ALTER COLUMN tenant_id SET NOT NULL;

ALTER TABLE public.fact_ingest_audit
  ALTER COLUMN tenant_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_dim_scope_tenant_id
  ON public.dim_scope (tenant_id);

CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_tenant_id
  ON public.fact_cost_daily (tenant_id);

CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_tenant_cost_date
  ON public.fact_cost_daily (tenant_id, cost_date);

CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_tenant_cloud_cost_date
  ON public.fact_cost_daily (tenant_id, cloud, cost_date);

CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_tenant_scope_cost_date
  ON public.fact_cost_daily (tenant_id, scope_id, cost_date);

CREATE INDEX IF NOT EXISTS ix_fact_cost_daily_tenant_service_cost_date
  ON public.fact_cost_daily (tenant_id, service_id, cost_date);

CREATE INDEX IF NOT EXISTS ix_ingest_job_tenant_id
  ON public.ingest_job (tenant_id);

CREATE INDEX IF NOT EXISTS ix_fact_ingest_audit_tenant_id
  ON public.fact_ingest_audit (tenant_id);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_tags_gin
  ON public.fact_cost_daily USING GIN (tags);

CREATE INDEX IF NOT EXISTS idx_fact_cost_daily_raw_gin
  ON public.fact_cost_daily USING GIN (raw);

COMMIT;
