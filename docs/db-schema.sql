--
-- PostgreSQL database dump
--

\restrict krQUfk9qPh84s46xOVkTuTKd2T4F5JV5qc93EluEHwmbnI4J4ecebMbW05A3e28

-- Dumped from database version 16.12 (Debian 16.12-1.pgdg13+1)
-- Dumped by pg_dump version 16.12 (Debian 16.12-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: cloud_provider; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.cloud_provider AS ENUM (
    'aws',
    'azure',
    'oci'
);


--
-- Name: job_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.job_status AS ENUM (
    'queued',
    'running',
    'success',
    'failed',
    'partial'
);


--
-- Name: scope_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.scope_type AS ENUM (
    'aws_account',
    'azure_subscription',
    'oci_tenancy',
    'oci_compartment',
    'unknown'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: dim_currency_rate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_currency_rate (
    rate_id uuid DEFAULT gen_random_uuid() NOT NULL,
    rate_date date NOT NULL,
    from_currency text NOT NULL,
    to_currency text NOT NULL,
    rate numeric(18,8) NOT NULL,
    source text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dim_region; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_region (
    region_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cloud public.cloud_provider NOT NULL,
    region_key text NOT NULL,
    region_name text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dim_scope; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_scope (
    scope_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cloud public.cloud_provider NOT NULL,
    scope_type public.scope_type DEFAULT 'unknown'::public.scope_type NOT NULL,
    scope_key text NOT NULL,
    scope_name text,
    parent_scope_key text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dim_service; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_service (
    service_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cloud public.cloud_provider NOT NULL,
    service_key text NOT NULL,
    service_name text NOT NULL,
    raw_service text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: fact_cost_daily; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_cost_daily (
    fact_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cost_date date NOT NULL,
    cloud public.cloud_provider NOT NULL,
    scope_id uuid,
    service_id uuid,
    region_id uuid,
    scope_key text NOT NULL,
    service_key text NOT NULL,
    region_key text,
    currency text DEFAULT 'USD'::text NOT NULL,
    amount numeric(18,6) DEFAULT 0 NOT NULL,
    amount_brl numeric(18,6),
    fx_rate_used numeric(18,8),
    charge_type text,
    pricing_model text,
    meter_category text,
    meter_subcategory text,
    resource_id text,
    resource_name text,
    tags jsonb DEFAULT '{}'::jsonb NOT NULL,
    source text DEFAULT 'unknown'::text NOT NULL,
    source_record_id text,
    raw jsonb DEFAULT '{}'::jsonb NOT NULL,
    job_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: fact_ingest_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_ingest_audit (
    audit_id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    cloud public.cloud_provider NOT NULL,
    fact_table text DEFAULT 'fact_cost_daily'::text NOT NULL,
    rows_inserted bigint DEFAULT 0 NOT NULL,
    rows_updated bigint DEFAULT 0 NOT NULL,
    rows_deleted bigint DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ingest_job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingest_job (
    job_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cloud public.cloud_provider NOT NULL,
    status public.job_status DEFAULT 'queued'::public.job_status NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    source text NOT NULL,
    source_window_start date,
    source_window_end date,
    dataset_version text,
    stats jsonb DEFAULT '{}'::jsonb NOT NULL,
    error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: dim_currency_rate dim_currency_rate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_currency_rate
    ADD CONSTRAINT dim_currency_rate_pkey PRIMARY KEY (rate_id);


--
-- Name: dim_currency_rate dim_currency_rate_rate_date_from_currency_to_currency_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_currency_rate
    ADD CONSTRAINT dim_currency_rate_rate_date_from_currency_to_currency_key UNIQUE (rate_date, from_currency, to_currency);


--
-- Name: dim_region dim_region_cloud_region_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_region
    ADD CONSTRAINT dim_region_cloud_region_key_key UNIQUE (cloud, region_key);


--
-- Name: dim_region dim_region_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_region
    ADD CONSTRAINT dim_region_pkey PRIMARY KEY (region_id);


--
-- Name: dim_scope dim_scope_cloud_scope_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_scope
    ADD CONSTRAINT dim_scope_cloud_scope_key_key UNIQUE (cloud, scope_key);


--
-- Name: dim_scope dim_scope_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_scope
    ADD CONSTRAINT dim_scope_pkey PRIMARY KEY (scope_id);


--
-- Name: dim_service dim_service_cloud_service_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_service
    ADD CONSTRAINT dim_service_cloud_service_key_key UNIQUE (cloud, service_key);


--
-- Name: dim_service dim_service_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_service
    ADD CONSTRAINT dim_service_pkey PRIMARY KEY (service_id);


--
-- Name: fact_cost_daily fact_cost_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_cost_daily
    ADD CONSTRAINT fact_cost_daily_pkey PRIMARY KEY (fact_id);


--
-- Name: fact_ingest_audit fact_ingest_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_ingest_audit
    ADD CONSTRAINT fact_ingest_audit_pkey PRIMARY KEY (audit_id);


--
-- Name: ingest_job ingest_job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingest_job
    ADD CONSTRAINT ingest_job_pkey PRIMARY KEY (job_id);


--
-- Name: idx_fact_cost_daily_cloud_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_cost_daily_cloud_date ON public.fact_cost_daily USING btree (cloud, cost_date);


--
-- Name: idx_fact_cost_daily_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_cost_daily_date ON public.fact_cost_daily USING btree (cost_date);


--
-- Name: idx_fact_cost_daily_raw_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_cost_daily_raw_gin ON public.fact_cost_daily USING gin (raw);


--
-- Name: idx_fact_cost_daily_region_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_cost_daily_region_date ON public.fact_cost_daily USING btree (cloud, region_key, cost_date);


--
-- Name: idx_fact_cost_daily_scope_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_cost_daily_scope_date ON public.fact_cost_daily USING btree (cloud, scope_key, cost_date);


--
-- Name: idx_fact_cost_daily_service_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_cost_daily_service_date ON public.fact_cost_daily USING btree (cloud, service_key, cost_date);


--
-- Name: idx_fact_cost_daily_tags_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_cost_daily_tags_gin ON public.fact_cost_daily USING gin (tags);


--
-- Name: uq_fact_cost_daily_natural_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_fact_cost_daily_natural_key ON public.fact_cost_daily USING btree (cost_date, cloud, scope_key, service_key, COALESCE(region_key, ''::text), COALESCE(resource_id, ''::text), currency, COALESCE(charge_type, ''::text), COALESCE(pricing_model, ''::text));


--
-- Name: fact_cost_daily fact_cost_daily_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_cost_daily
    ADD CONSTRAINT fact_cost_daily_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.ingest_job(job_id) ON DELETE SET NULL;


--
-- Name: fact_cost_daily fact_cost_daily_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_cost_daily
    ADD CONSTRAINT fact_cost_daily_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.dim_region(region_id);


--
-- Name: fact_cost_daily fact_cost_daily_scope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_cost_daily
    ADD CONSTRAINT fact_cost_daily_scope_id_fkey FOREIGN KEY (scope_id) REFERENCES public.dim_scope(scope_id);


--
-- Name: fact_cost_daily fact_cost_daily_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_cost_daily
    ADD CONSTRAINT fact_cost_daily_service_id_fkey FOREIGN KEY (service_id) REFERENCES public.dim_service(service_id);


--
-- Name: fact_ingest_audit fact_ingest_audit_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_ingest_audit
    ADD CONSTRAINT fact_ingest_audit_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.ingest_job(job_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict krQUfk9qPh84s46xOVkTuTKd2T4F5JV5qc93EluEHwmbnI4J4ecebMbW05A3e28

