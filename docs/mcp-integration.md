# MCP para IA Especialista em SQL e Comparacao Multi-Cloud

## E possivel?
Sim. O projeto ja possui base ideal para isso: API FinOps consolidada, modelo SQL multi-tenant e endpoints por cloud (aws, azure, oci). Um MCP dedicado pode atuar como camada de inteligencia para traduzir perguntas em consultas SQL seguras e comparacoes entre clouds.

## Objetivo
Criar um "FinOps SQL MCP" para:
- responder perguntas em linguagem natural com foco em SQL analitico;
- comparar custo, tendencia, variacao e concentracao entre AWS, Azure e OCI;
- combinar consultas diretas ao banco com chamadas aos endpoints existentes do sistema.

## Pontos do sistema que o MCP deve chamar
Endpoints ja existentes no backend:
- `GET /finops/summary`
- `GET /finops/daily`
- `GET /finops/top-services`
- `GET /finops/top-accounts`
- `GET /finops/filters`
- `GET /finops/cost-explorer/snapshot`
- `GET /finops/cost-explorer/breakdown`
- `GET /finops/cost-explorer/trend`
- `POST /finops/reingest`
- `GET /cloud/{cloud}/tenants`

## Base SQL alvo para o MCP
Tabelas principais para analise:
- `public.fact_cost_daily`
- `public.dim_scope`
- `public.dim_service`
- `public.dim_region`
- `public.dim_tenant` (criada no script multi-tenant)

## Arquitetura sugerida
1. Cliente IA (chat interno ou assistente do dashboard)
2. MCP Server `finops-sql-mcp`
3. Conectores do MCP:
- `sql_readonly_adapter` (PostgreSQL)
- `finops_api_adapter` (chamada HTTP interna para `/finops/*`)
4. Camada de seguranca SQL
- somente `SELECT`
- bloqueio de `INSERT/UPDATE/DELETE/DDL`
- limite de linhas (ex.: 500)
- timeout curto (ex.: 10s)
- escopo obrigatorio por `cloud` e `tenant_key` quando aplicavel

## Ferramentas MCP (tools) recomendadas
- `sql.explain_query`
  - Recebe pergunta + filtros e devolve plano SQL proposto antes da execucao.
- `sql.run_readonly`
  - Executa SQL validado em modo read-only e retorna dados tabulares.
- `finops.get_summary`
  - Wrapper para `GET /finops/summary`.
- `finops.get_daily`
  - Wrapper para `GET /finops/daily`.
- `finops.get_breakdown`
  - Wrapper para `GET /finops/cost-explorer/breakdown`.
- `finops.get_tenants`
  - Wrapper para `GET /cloud/{cloud}/tenants`.
- `finops.compare_clouds`
  - Orquestra multiplas chamadas (ou SQL unico) para comparar clouds no mesmo periodo e moeda.

## Tipos de comparacao que o MCP deve suportar
- Custo total por cloud no periodo.
- Variacao percentual cloud vs cloud.
- Tendencia semanal e mensal por cloud.
- Top servicos por cloud e divergencia entre clouds.
- Top contas/scopes por cloud.
- Participacao percentual de cada cloud no total (share).
- Outliers de custo por dia/servico/cloud.

## Exemplo de fluxo
Pergunta: "Compare AWS vs Azure nos ultimos 30 dias em BRL e mostre top 5 servicos com maior diferenca."
1. MCP resolve tenants validos por cloud (`/cloud/{cloud}/tenants`).
2. MCP monta SQL padrao com `fact_cost_daily` + `dim_service`.
3. MCP executa consulta read-only com filtros de data, moeda, cloud e tenant.
4. MCP devolve:
- tabela comparativa
- variacao percentual
- resumo executivo curto
- recomendacoes de investigacao

## Exemplo SQL (base)
```sql
SELECT
  f.cloud,
  s.service_name,
  SUM(f.cost_amount) AS total_cost
FROM public.fact_cost_daily f
JOIN public.dim_service s ON s.service_id = f.service_id
JOIN public.dim_tenant t ON t.tenant_id = f.tenant_id
WHERE f.cost_date BETWEEN :from_date AND :to_date
  AND f.currency = :currency
  AND f.cloud IN ('aws', 'azure')
  AND t.tenant_key IN (:tenant_aws, :tenant_azure)
GROUP BY f.cloud, s.service_name
ORDER BY total_cost DESC
LIMIT 200;
```

## Regras de qualidade
- Sempre normalizar moeda antes de comparar.
- Sempre explicitar periodo e tenant usados na resposta.
- Sempre retornar query SQL gerada para auditoria.
- Sempre validar cobertura de dados (evitar conclusao com lacuna silenciosa).

## MVP em 3 fases
1. Fase 1 (rapida)
- `sql.run_readonly`, `finops.get_summary`, `finops.get_daily`, `finops.get_tenants`.
- Comparacoes basicas AWS/Azure/OCI.
2. Fase 2
- `finops.compare_clouds` com templates de analise e ranking de diferencas.
- Explicacao automatica do "por que" da variacao.
3. Fase 3
- Insights proativos: alertas de anomalia e recomendacoes de acao.
- Memoria curta por tenant (preferencias de consulta e metricas favoritas).

## Ganho esperado
- Menos analise manual em SQL ad-hoc.
- Respostas comparativas consistentes entre clouds.
- Maior velocidade para investigacao de custo e tomada de decisao FinOps.
