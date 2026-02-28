# FinOps Multicloud Frontend

Frontend Next.js (App Router) para painel FinOps Multicloud com shell enterprise: sidebar de navegação, topbar global, drawer de filtros avançados e módulos funcionais.

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

- `/overview`: visão geral principal
- `/analytics`: gráficos e tabelas operacionais
- `/cost-explorer`: workspace para breakdowns
- `/trends`: evolução temporal
- `/budgets`: metas versus execução
- `/ai`: assistente e insights
- `/settings`: preferências do workspace
- `/dashboard`: rota legada mantida, apontando para overview ou IA via `?tab=ai`
- `/dashboard/weekly`: detalhamento semanal legado

## Novo layout

- `src/components/layout/AppShell.tsx`: shell principal com sidebar, topbar e workspace.
- `src/components/layout/Topbar.tsx`: filtros globais de cloud, período, moeda, compare e refresh.
- `src/components/layout/FilterDrawer.tsx`: filtros avançados de `topN`, serviços e linked accounts.
- `src/components/layout/SidebarNav.tsx`: navegação lateral colapsável.
- `src/contexts/AppContext.tsx`: estado global de UI e preferências locais.

## Como os filtros funcionam

- Filtros principais continuam serializados na URL (`cloud`, `from`, `to`, `currency`, `topN`, `services`, `accounts`).
- `useDashboardFilters` mantém compatibilidade com os endpoints atuais e preserva outros query params, como `tab=ai`.
- Preferências de layout (`compareMode`, sidebar colapsada e saved views) ficam em `localStorage`.
- O drawer apenas muda a UI dos filtros avançados; as chamadas do backend permanecem as mesmas.

## Mocks tipados

Fixtures em `src/lib/mocks/fixtures.ts`, roteadas por `src/lib/mocks/mock-api.ts`.

Com isso, a UI roda sem backend e mantém o contrato de API validado por Zod.
