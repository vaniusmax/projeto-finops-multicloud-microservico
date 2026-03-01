# FinOps Micro Backend

API RESTful FastAPI para analytics FinOps usando Postgres canônico v0.

## Rodar local (uv)

```bash
cd finops-micro/backend
uv venv
uv sync
cp .env.example .env
uv run alembic upgrade head
uvicorn finops_api.main:app --reload --port 8000
```

## Rodar local (pip)

```bash
cd finops-micro/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m alembic upgrade head
uvicorn finops_api.main:app --reload --port 8000
```

## Testes

```bash
python -m pytest
```

## Atalhos com Makefile

```bash
cd finops-micro/backend
make install
make migrate
make run
```

Se o `.env` estiver apontando para rede interna Docker (`finops-db`), rode:

```bash
make migrate-local
```

## Ingestao via CLI dos cloud providers

Com variaveis no `.env` e CLIs autenticadas (`aws`, `az`, `oci`):

```bash
cd finops-micro/backend
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider aws --start 2026-01-01 --end 2026-01-31
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider azure --start 2026-01-01 --end 2026-01-31
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider oci --start 2026-01-01 --end 2026-01-31
.venv/bin/python -m finops_api.jobs.ingest_cli providers --provider all --start 2026-01-01 --end 2026-01-31
```

Auto-ingest no carregamento do frontend:
- Ao chamar `summary`, `timeseries` ou `top-services`, a API tenta ingestao CLI automaticamente quando nao ha dados no intervalo solicitado.
- Controle por env: `AUTO_INGEST_ON_REQUEST=true|false`.

## Cotacao USD/BRL com Agno

O backend continua persistindo a cotacao em `dim_currency_rate`, mas agora pode usar Agno + OpenAI + YFinance para buscar a taxa corrente antes do fallback HTTP.

Ordem de tentativa para datas correntes:
- `AgnoAgent` com `OpenAIChat` e `YFinanceTools`
- `YFinanceTools` direto
- provider HTTP configurado em `CURRENCY_RATE_PROVIDER_URL`

Configuracao opcional no `.env`:
- `CURRENCY_RATE_AGNO_ENABLED=true`
- `CURRENCY_RATE_YFINANCE_ENABLED=true`
- `OPENAI_API_KEY=...`
- `OPENAI_MODEL=gpt-4o-mini`
- `OPENAI_API_BASE=` opcional

Se Agno/OpenAI nao estiverem disponiveis, a arquitetura atual segue funcionando via HTTP e persistencia normal na tabela canônica.
