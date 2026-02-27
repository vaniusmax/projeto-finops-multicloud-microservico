# FinOps Multicloud Frontend

Frontend Next.js (App Router) para painel FinOps Multicloud com sidebar de filtros, dashboard interativo, drilldown semanal e assistente de IA.

## Stack

- Next.js 14+ (App Router) + TypeScript
- TailwindCSS
- Componentes estilo shadcn/ui (`Button`, `Card`, `Tabs`, `Select`, `Badge`, `Input`, `Dialog`, `Tooltip`)
- TanStack Query (React Query)
- TanStack Table
- Recharts
- Zod
- ESLint + Prettier

## Como rodar

```bash
npm install
npm run dev
```

Aplicação em `http://localhost:3000`.

## Variáveis de ambiente

Crie `.env.local`:

```env
NEXT_PUBLIC_API_GATEWAY_URL=
NEXT_PUBLIC_FINOPS_SERVICE_URL=
NEXT_PUBLIC_API_BASE_PATH=/api/v1
NEXT_PUBLIC_USE_MOCKS=false
```

## Gateway x Microservice

A seleção de base URL funciona assim:

1. Se `NEXT_PUBLIC_API_GATEWAY_URL` estiver definido, ele é usado.
2. Senão, usa `NEXT_PUBLIC_FINOPS_SERVICE_URL`.
3. O frontend prefixa rotas com `NEXT_PUBLIC_API_BASE_PATH` (default `/api/v1`).
4. Se nenhum estiver definido (ou `NEXT_PUBLIC_USE_MOCKS=true`), usa mocks tipados locais.

## Endpoints consumidos

- `GET /finops/summary`
- `GET /finops/daily`
- `GET /finops/top-services`
- `GET /finops/top-accounts`
- `GET /finops/filters`
- `POST /finops/ai/insights`

## Rotas da UI

- `/dashboard`: visão geral com KPIs, barras, linha, tabelas e aba IA
- `/dashboard/weekly`: visão detalhada semanal

## Mocks tipados

Fixtures em `src/lib/mocks/fixtures.ts`, roteadas por `src/lib/mocks/mock-api.ts`.

Com isso, a UI roda sem backend e mantém o contrato de API validado por Zod.
