# FinOps Micro (Monorepo)

Nova versão do `projeto-finops-multicloud` com arquitetura de serviços HTTP:
- Backend: FastAPI + SQLAlchemy + Alembic
- Banco: PostgreSQL (modelo canônico v0)
- Frontend: Next.js (App Router)

## Estrutura

- `backend/`: API `/api/v1`, serviços, repositórios, ingestão CLI e migrations.
- `frontend/`: dashboard FinOps (filtros, KPIs, gráficos, tabelas, IA).
- `infra/`: `docker-compose`, variáveis de ambiente e seed SQL.
- `../projeto-finops-multicloud/`: sistema legado usado como referência de regra.

## Como frontend e backend interagem

Fluxo no carregamento de `/dashboard`:

1. O frontend lê filtros da URL (`cloud`, `from`, `to`, `currency`, `topN`, `services`, `accounts`).
2. Com React Query, dispara em paralelo:
   - `GET /api/v1/finops/summary`
   - `GET /api/v1/finops/daily`
   - `GET /api/v1/finops/top-services`
   - `GET /api/v1/finops/top-accounts`
   - `GET /api/v1/finops/filters`
3. O backend passa pelo `AutoIngestService` (quando `AUTO_INGEST_ON_REQUEST=true`), e só depois agrega dados.
4. O frontend valida respostas com Zod antes de renderizar cards, gráficos e grids.

### Mapeamento UI -> endpoint

- Cards de visão geral: `GET /finops/summary`
- Gráfico de barras "ANÁLISE DE DADOS": `GET /finops/top-accounts` (top linked accounts)
- Grid "DADOS: LINKED ACCOUNT": `GET /finops/top-accounts`
- Gráfico de linhas "GRÁFICO DE LINHAS": `GET /finops/daily` (séries por serviço em `byService`)
- Grid "DADOS DO GRÁFICO DE LINHAS": `GET /finops/top-services`
- Assistente IA: `POST /finops/ai/insights`

### Resolução de base URL no frontend

Arquivo: `frontend/src/lib/api/http.ts`

Ordem de fallback:
1. `NEXT_PUBLIC_API_GATEWAY_URL`
2. `NEXT_PUBLIC_FINOPS_SERVICE_URL`
3. `NEXT_PUBLIC_API_BASE_URL`
4. se vazio, usa mocks tipados locais (`NEXT_PUBLIC_USE_MOCKS=true` ou ausência de base URL)

## Comportamento automático de carga de dados

Não existe botão manual para "carregar AWS" no fluxo principal.

O carregamento é automático:
- Ao chamar os endpoints `/finops/*`, o backend verifica se já existem dados no intervalo.
- Se faltar dado, executa ingestão via CLI (`aws`, `az`, `oci`) no request atual.
- Para AWS, exige as duas fontes para considerar o período completo:
  - `aws_ce_service_cli` (serviços)
  - `aws_ce_account_cli` (contas)

## Endpoints ativos

### Contrato principal (usado pelo frontend atual)

- `GET /api/v1/finops/summary?cloud&from&to&currency`
- `GET /api/v1/finops/daily?cloud&from&to&currency&topN&services&accounts`
- `GET /api/v1/finops/top-services?cloud&from&to&currency&topN`
- `GET /api/v1/finops/top-accounts?cloud&from&to&currency&topN`
- `GET /api/v1/finops/filters?cloud&month`
- `POST /api/v1/finops/ai/insights`
- `POST /api/v1/finops/reingest` (endpoint auxiliar)

### Contrato legado ainda exposto (não usado no frontend novo)

- `GET /api/v1/summary?cloud&start&end`
- `GET /api/v1/timeseries?cloud&start&end&granularity=daily`
- `GET /api/v1/top-services?cloud&start&end&limit`
- `GET /api/v1/filters?cloud`

## Divergências e códigos sem nexo (estado atual)

1. Há dois contratos HTTP coexistindo (`/api/v1/*` legado e `/api/v1/finops/*` novo), com parâmetros diferentes (`start/end` vs `from/to`), o que aumenta risco de uso incorreto.
2. `frontend/src/lib/api/http.ts` suporta `NEXT_PUBLIC_API_BASE_URL`, mas essa variável não está alinhada com a documentação principal do frontend (que prioriza gateway/serviço).
3. `infra/.env.example` define `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`; como o cliente também prefixa `NEXT_PUBLIC_API_BASE_PATH` por padrão (`/api/v1`), pode gerar base duplicada (`/api/v1/api/v1`) se configurado sem cuidado.
4. `frontend/.env.local` contém variáveis de backend e banco (`POSTGRES_*`, `DATABASE_URL`, `CORS_ORIGINS`) que não são usadas no app Next.js.
5. `frontend/src/lib/api/finops.ts` expõe `postReingest`, mas não há uso na UI atual.
6. Existem `TODO`s de paridade com legado:
   - `backend/src/finops_api/services/analytics_service.py`
   - `backend/src/finops_api/providers/registry.py`

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

Ingestão via CLIs dos providers:

```bash
cd finops-micro/backend
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider all --start 2026-01-01 --end 2026-01-31
```

## Frontend local

```bash
cd finops-micro/frontend
npm install
npm run dev
```
