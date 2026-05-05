.PHONY: install migrate migrate-local run test ingest-all

install:
	uv sync

migrate:
	uv run alembic upgrade head

migrate-local:
	DATABASE_URL=postgresql+psycopg2://finops:finops123@127.0.0.1:5432/finops uv run alembic upgrade head

run:
	uv run uvicorn finops_api.main:app --reload --port 8000

test:
	uv run pytest -q

ingest-all:
	uv run python -m finops_api.jobs.ingest_cli providers --provider all
