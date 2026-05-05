# FinOps Micro

Monorepo da aplicação FinOps Multicloud.

## Escopo deste diretório

- `backend/`: API FastAPI, regras de ingestão e analytics, migrations Alembic.
- `frontend/`: dashboard Next.js (App Router).

Infraestrutura e operação de ambientes (Traefik, Postgres, deploy Docker):

- `../finops-traefik-stack/`

## Fonte de verdade por domínio

- Aplicação backend: `finops-micro/backend/`
- Aplicação frontend: `finops-micro/frontend/`
- Infra e deploy: `finops-traefik-stack/`
- Evolução de schema: `backend/src/finops_api/db/migrations/versions`

## Contrato principal atual

A API consumida pelo frontend está sob `API_PREFIX=/api/v1` e usa principalmente:

- `/api/v1/auth/*`
- `/api/v1/cloud/*`
- `/api/v1/finops/*`

## Desenvolvimento local rápido

### Backend

```bash
cd finops-micro/backend
uv venv
uv sync --extra dev
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn finops_api.main:app --reload --port 8000
```

### Frontend

```bash
cd finops-micro/frontend
npm install
npm run dev
```

Crie `finops-micro/frontend/.env.local`:

```env
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api/v1
NEXT_PUBLIC_USE_MOCKS=false
```

## Ambiente completo com Docker

Para subir banco, proxy e aplicações no fluxo oficial:

- `../finops-traefik-stack/README.md`

Resumo do fluxo oficial:

```bash
cd ../finops-traefik-stack
make up
make sql-init      # primeira execução
make migrate
make app-up
```

## Deploy de produção

Use apenas a stack:

- `finops-traefik-stack/`

Guia oficial:

- `finops-traefik-stack/README.md`

Observação: no deploy por Docker Hub, execute `make migrate` antes de `make hub-deploy`.
