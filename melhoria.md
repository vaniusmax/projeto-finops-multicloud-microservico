# Proposta de Melhoria Arquitetural

Objetivo: evoluir a arquitetura sem quebrar API/UI, em 5 PRs pequenos e reversíveis.

## 1) Strategy + Factory para ingestão multicloud (prioridade alta, 1-2 dias)

- Motivo: remover `if/elif` de provider no core.
- Mudança: criar interface `CostProviderStrategy` + `ProviderFactory/Registry`.
- Arquivos alvo: `ingest_service.py`, `aws/cli_client.py`, `azure/cli_client.py`, `oci/cli_client.py`, novo `providers/registry.py`.
- Critério de aceite: ingestão `aws|azure|oci|all` funcionando com mesmo contrato atual.

## 2) Use Case / Command Handler nos endpoints FinOps (alta, 2-3 dias)

- Motivo: reduzir orquestração dentro do router.
- Mudança: extrair casos de uso (`GetSummaryUseCase`, `GetDailyUseCase`, `ReingestUseCase`, etc.) e deixar router fino.
- Arquivos alvo: `routers/finops.py`, novo `application/use_cases/*`.
- Critério de aceite: assinatura HTTP e payloads idênticos.

## 3) Specification Pattern para filtros de consulta (média, 2 dias)

- Motivo: centralizar regras de filtro SQL e evitar duplicação.
- Mudança: criar `specifications` compostas (`CloudSpec`, `TenantSpec`, `DateRangeSpec`, `ServiceSpec`, `AccountSpec`) aplicadas no repositório.
- Arquivos alvo: `fact_cost_repo.py`.
- Critério de aceite: resultados iguais aos atuais em testes de regressão.

## 4) State Machine para IngestJob (média, 1-2 dias)

- Motivo: impedir transições inválidas de status.
- Mudança: encapsular transições (`pending -> running -> success|failed|cancelled`) com validação.
- Arquivos alvo: `ingest_job.py`, `services/ingest_job_service.py`.
- Critério de aceite: transições inválidas bloqueadas e auditáveis.

## 5) Circuit Breaker + Bulkhead para chamadas CLI (alta para operação, 2 dias)

- Motivo: retry sozinho não evita cascata quando provider externo cai.
- Mudança: circuit breaker por provider/tenant com janela de falha, cooldown e fallback controlado; isolamento de execução por provider.
- Arquivos alvo: `providers/common/__init__.py`, `auto_ingest_service.py`.
- Critério de aceite: sob falha repetida de CLI, API degrada de forma previsível e não entra em tempestade de retries.

## Plano de Entrega

1. PR1 e PR2 primeiro (maior ganho de manutenção).
2. PR3 em seguida (estabiliza repositório).
3. PR4 e PR5 fecham robustez operacional.

## Estimativa Total

- 8 a 11 dias úteis, com rollout incremental e sem breaking change de contrato.
