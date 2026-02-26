# FinOps Micro (Monorepo)

Nova versão do `projeto-finops-multicloud` em arquitetura de microserviços RESTful:
- Backend: FastAPI + SQLAlchemy + Alembic
- Banco: Postgres (modelo canônico v0)
- Frontend: Next.js

## Estrutura

- `backend/`: API `/api/v1` + camada service/repository + migrations
- `frontend/`: dashboard MVP com cards, filtros e timeseries
- `infra/`: docker compose, env e init SQL

## Subir com Docker

```bash
cd finops-micro/infra
cp .env.example .env
docker compose up -d --build
```

Serviços:
- API: `http://localhost:8000`
- Frontend: `http://localhost:3000/dashboard`
- Postgres: `localhost:5432`

## Backend local

```bash
cd finops-micro/backend
uv venv
uv sync
cp .env.example .env
uv run alembic upgrade head
uvicorn finops_api.main:app --reload --port 8000
```

Alternativa com pip:

```bash
cd finops-micro/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m alembic upgrade head
uvicorn finops_api.main:app --reload --port 8000
```

Ingestao via CLIs dos providers:

```bash
cd finops-micro/backend
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider all --start 2026-01-01 --end 2026-01-31
```

## Frontend local

```bash
cd finops-micro/frontend
npm install
cp ../infra/.env.example .env.local
npm run dev
```

## Endpoints MVP

- `GET /api/v1/health`
- `GET /api/v1/filters?cloud=all`
- `GET /api/v1/summary?cloud=all&start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/v1/timeseries?cloud=all&start=YYYY-MM-DD&end=YYYY-MM-DD&granularity=daily`
- `GET /api/v1/top-services?cloud=all&start=YYYY-MM-DD&end=YYYY-MM-DD&limit=10`

## Reaproveitamento do legado

O legado em `projeto-finops-multicloud/app/providers` e `app/services` foi usado como referência para:
- clouds canônicas `aws|azure|oci`
- filtros por período, serviço e scope
- agregações por SQL para top serviços e séries temporais

Diferenças entre agregações antigas e canônicas foram marcadas com `TODO` em `backend/src/finops_api/services` e `backend/src/finops_api/providers`.
