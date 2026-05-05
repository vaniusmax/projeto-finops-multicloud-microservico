# FinOps Micro Backend

API FastAPI responsável por autenticação, tenants por cloud, ingestão (AWS/Azure/OCI) e analytics FinOps.

## Stack

- Python 3.13
- FastAPI + SQLAlchemy + Alembic
- PostgreSQL
- Ingestão via CLIs: `aws`, `az`, `oci`

## Pré-requisitos

- Python 3.13
- `uv` (gerenciador de ambiente/dependências)
- PostgreSQL acessível pelo `DATABASE_URL`
- CLIs de cloud autenticadas quando houver ingestão manual/automática

## Configuração

```bash
cd finops-micro/backend
cp .env.example .env
```

Variáveis importantes:

- API e CORS: `API_PREFIX`, `CORS_ORIGINS`, `CORS_ORIGIN_REGEX`
- Banco: `DATABASE_URL`
- Ingestão automática: `AUTO_INGEST_ON_REQUEST`
- Clouds: `AWS_*`, `AZURE_*`, `OCI_*`, `TENANT_CONFIGS_JSON`
- Metas: `TARGET_*`, `MONTHLY_TARGETS_JSON`
- Câmbio USD/BRL: `CURRENCY_RATE_*`, `USD_RATE_FALLBACK`
- IA (insights): `OPENAI_API_KEY`, `OPENAI_MODEL` (default: `gpt-5.4`), `OPENAI_API_BASE`
- Auth/e-mail: `AUTH_*`, `SMTP_*`

## Rodar local (uv)

```bash
cd finops-micro/backend
uv venv
uv sync --extra dev
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn finops_api.main:app --reload --port 8000
```

## Makefile (atalhos)

```bash
cd finops-micro/backend
make install
make migrate
make run
make test
```

Se precisar forçar host local do Postgres:

```bash
make migrate-local
```

## Endpoints ativos (`/api/v1`)

### Health

- `GET /health`

### Auth

- `POST /auth/register`
- `POST /auth/verify-email`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`

### Cloud

- `GET /cloud/{cloud}/tenants`

`cloud` aceito: `aws`, `azure`, `oci`.

### FinOps

- `GET /finops/summary`
- `GET /finops/daily`
- `GET /finops/top-services`
- `GET /finops/top-accounts`
- `GET /finops/filters`
- `POST /finops/ai/insights`
- `POST /finops/analytics/insights`
- `GET /finops/cost-explorer/snapshot`
- `GET /finops/cost-explorer/breakdown`
- `GET /finops/cost-explorer/trend`
- `POST /finops/cost-explorer/insights`
- `POST /finops/reingest`

Parâmetros principais de analytics:

- `cloud=aws|azure|oci|all`
- `tenant_key` (quando multi-tenant por cloud)
- `from`, `to` (intervalo)
- `currency=BRL|USD`
- `topN` (quando aplicável)

## Ingestão por CLI (manual)

Com `.env` configurado e CLIs autenticadas:

```bash
cd finops-micro/backend
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider aws --start 2026-01-01 --end 2026-01-31
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider azure --start 2026-01-01 --end 2026-01-31
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider oci --start 2026-01-01 --end 2026-01-31
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider all --start 2026-01-01 --end 2026-01-31
```

## Auto-ingest e refresh

- Com `AUTO_INGEST_ON_REQUEST=true`, a API tenta preencher lacunas do período sob demanda.
- Para forçar recarga no request, use `refresh=true` nos endpoints `GET /finops/*`.
- Para reprocessamento explícito, use `POST /finops/reingest`.

## Migrations e schema

Fonte de verdade evolutiva:

- `src/finops_api/db/migrations/versions`

Comandos úteis:

```bash
uv run alembic current
uv run alembic upgrade head
```

## Testes

```bash
cd finops-micro/backend
uv run pytest -q
```

## Produção (container)

- A imagem de produção usa base com AWS CLI, Azure CLI e OCI CLI pré-instaladas (`Dockerfile.base-clls`).
- No deploy via `finops-traefik-stack`, a operação oficial usa `docker-compose.yml` unificado com profiles.
- Migrations em produção devem rodar via serviço isolado `finops-api-migrate` (`make migrate` na stack), não no startup do backend.
