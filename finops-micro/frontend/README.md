# FinOps Multicloud Frontend

Frontend Next.js do workspace FinOps (overview, analytics, cost explorer, tendências, budgets, IA e configurações).

## Stack

- Next.js 14 (App Router) + TypeScript
- TailwindCSS
- React Query (TanStack Query)
- Recharts
- Zod

## Pré-requisitos

- Node.js 22+
- npm

## Executar localmente

```bash
cd finops-micro/frontend
npm install
npm run dev
```

Aplicação: `http://localhost:3000`

## Scripts

- `npm run dev`: desenvolvimento com `NEXT_DIST_DIR=.next-dev`
- `npm run dev:warmup`: dev com prewarm de rotas
- `npm run dev:raw`: dev direto sem prewarm
- `npm run build`: build de produção (usa `.next`)
- `npm run start`: start de produção local
- `npm run serve:stable`: build + start
- `npm run lint`: lint

## Variáveis de ambiente

Crie `.env.local`:

```env
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api/v1
NEXT_PUBLIC_USE_MOCKS=false
```

Resolução de base URL:

1. Usa `NEXT_PUBLIC_API_GATEWAY_URL` como host base.
2. Prefixa rotas com `NEXT_PUBLIC_API_BASE_PATH`.
3. Se o gateway estiver vazio ou `NEXT_PUBLIC_USE_MOCKS=true`, usa mocks locais tipados.

## Contrato de API consumido

Com `API_BASE_PATH=/api/v1`, o frontend usa:

### Auth

- `POST /auth/register`
- `POST /auth/verify-email`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`

### Cloud

- `GET /cloud/{cloud}/tenants`

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

## Rotas da UI

- `/overview`
- `/analytics`
- `/cost-explorer`
- `/trends`
- `/budgets`
- `/ai`
- `/settings`
- `/login`
- `/verify-email`

Rotas legadas mantidas por compatibilidade:

- `/dashboard`
- `/dashboard/weekly`

## Filtros e estado

- Filtros de negócio na URL: `cloud`, `tenant`, `from`, `to`, `currency`, `topN`, `services`, `accounts`.
- Preferências de UI (compare mode, sidebar, saved views) em `localStorage`.

## Mocks tipados

- Fixtures: `src/lib/mocks/fixtures.ts`
- Mock router: `src/lib/mocks/mock-api.ts`

## Build de produção (Docker)

O `Dockerfile.prod` recebe:

- `NEXT_PUBLIC_API_GATEWAY_URL`
- `NEXT_PUBLIC_API_BASE_PATH`
- `NEXT_PUBLIC_USE_MOCKS`

No fluxo oficial, esses valores vêm de `finops-traefik-stack/.env.frontend`.
