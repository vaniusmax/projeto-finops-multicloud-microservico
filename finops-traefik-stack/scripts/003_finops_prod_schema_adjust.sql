-- ==========================================================
-- FinOps Prod Schema Adjust (idempotente)
-- Alvo: alinhar schema real com Alembic head (0003_auth)
-- Data: 2026-03-26
-- ==========================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------
-- 1) Garantir tabelas de auth (Alebmic 0003_auth)
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.auth_user (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name VARCHAR(128) NOT NULL,
  last_name VARCHAR(128) NOT NULL,
  email VARCHAR(320) NOT NULL,
  password_hash VARCHAR(512) NULL,
  is_email_verified BOOLEAN NOT NULL DEFAULT false,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.auth_user'::regclass
      AND conname = 'uq_auth_user_email'
  ) THEN
    ALTER TABLE public.auth_user
      ADD CONSTRAINT uq_auth_user_email UNIQUE (email);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS ix_auth_user_email
  ON public.auth_user (email);

CREATE TABLE IF NOT EXISTS public.auth_email_verification_token (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  token_hash VARCHAR(128) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.auth_email_verification_token'::regclass
      AND conname = 'fk_auth_email_verification_token_user_id_auth_user'
  ) THEN
    ALTER TABLE public.auth_email_verification_token
      ADD CONSTRAINT fk_auth_email_verification_token_user_id_auth_user
      FOREIGN KEY (user_id) REFERENCES public.auth_user(user_id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.auth_email_verification_token'::regclass
      AND conname = 'uq_auth_email_verification_token_token_hash'
  ) THEN
    ALTER TABLE public.auth_email_verification_token
      ADD CONSTRAINT uq_auth_email_verification_token_token_hash UNIQUE (token_hash);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS ix_auth_email_verification_token_user_id
  ON public.auth_email_verification_token (user_id);

CREATE TABLE IF NOT EXISTS public.auth_session (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  token_hash VARCHAR(128) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ NULL,
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.auth_session'::regclass
      AND conname = 'fk_auth_session_user_id_auth_user'
  ) THEN
    ALTER TABLE public.auth_session
      ADD CONSTRAINT fk_auth_session_user_id_auth_user
      FOREIGN KEY (user_id) REFERENCES public.auth_user(user_id) ON DELETE CASCADE;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.auth_session'::regclass
      AND conname = 'uq_auth_session_token_hash'
  ) THEN
    ALTER TABLE public.auth_session
      ADD CONSTRAINT uq_auth_session_token_hash UNIQUE (token_hash);
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS ix_auth_session_user_id
  ON public.auth_session (user_id);

-- ----------------------------------------------------------
-- 2) Normalizacao de objetos duplicados (SQL bootstrap x Alembic)
-- ----------------------------------------------------------

-- dim_scope: manter nome de constraint usado no Alembic (uq_dim_scope_tenant_id)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'public.dim_scope'::regclass
      AND conname = 'uq_dim_scope_tenant_scope_key'
  ) THEN
    IF EXISTS (
      SELECT 1
      FROM pg_constraint
      WHERE conrelid = 'public.dim_scope'::regclass
        AND conname = 'uq_dim_scope_tenant_id'
    ) THEN
      ALTER TABLE public.dim_scope DROP CONSTRAINT uq_dim_scope_tenant_scope_key;
    ELSE
      ALTER TABLE public.dim_scope RENAME CONSTRAINT uq_dim_scope_tenant_scope_key TO uq_dim_scope_tenant_id;
    END IF;
  END IF;
END$$;

-- fact_cost_daily.tags GIN: manter ix_fact_cost_daily_tags_gin
DO $$
BEGIN
  IF to_regclass('public.ix_fact_cost_daily_tags_gin') IS NULL
     AND to_regclass('public.idx_fact_cost_daily_tags_gin') IS NOT NULL THEN
    ALTER INDEX public.idx_fact_cost_daily_tags_gin RENAME TO ix_fact_cost_daily_tags_gin;
  ELSIF to_regclass('public.ix_fact_cost_daily_tags_gin') IS NOT NULL
     AND to_regclass('public.idx_fact_cost_daily_tags_gin') IS NOT NULL THEN
    DROP INDEX IF EXISTS public.idx_fact_cost_daily_tags_gin;
  END IF;

  IF to_regclass('public.ix_fact_cost_daily_tags_gin') IS NULL THEN
    CREATE INDEX ix_fact_cost_daily_tags_gin
      ON public.fact_cost_daily USING gin (tags);
  END IF;
END$$;

-- fact_cost_daily.raw GIN: manter ix_fact_cost_daily_raw_gin
DO $$
BEGIN
  IF to_regclass('public.ix_fact_cost_daily_raw_gin') IS NULL
     AND to_regclass('public.idx_fact_cost_daily_raw_gin') IS NOT NULL THEN
    ALTER INDEX public.idx_fact_cost_daily_raw_gin RENAME TO ix_fact_cost_daily_raw_gin;
  ELSIF to_regclass('public.ix_fact_cost_daily_raw_gin') IS NOT NULL
     AND to_regclass('public.idx_fact_cost_daily_raw_gin') IS NOT NULL THEN
    DROP INDEX IF EXISTS public.idx_fact_cost_daily_raw_gin;
  END IF;

  IF to_regclass('public.ix_fact_cost_daily_raw_gin') IS NULL THEN
    CREATE INDEX ix_fact_cost_daily_raw_gin
      ON public.fact_cost_daily USING gin (raw);
  END IF;
END$$;

-- ----------------------------------------------------------
-- 3) Guard rails de consistencia para producao
-- ----------------------------------------------------------

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.dim_scope WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Schema invalido: dim_scope.tenant_id contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.fact_cost_daily WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Schema invalido: fact_cost_daily.tenant_id contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.fact_cost_daily WHERE scope_id IS NULL) THEN
    RAISE EXCEPTION 'Schema invalido: fact_cost_daily.scope_id contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.ingest_job WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Schema invalido: ingest_job.tenant_id contem NULL';
  END IF;
  IF EXISTS (SELECT 1 FROM public.fact_ingest_audit WHERE tenant_id IS NULL) THEN
    RAISE EXCEPTION 'Schema invalido: fact_ingest_audit.tenant_id contem NULL';
  END IF;
END$$;

COMMIT;

