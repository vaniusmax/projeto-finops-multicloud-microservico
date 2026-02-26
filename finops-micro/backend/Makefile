PYTHON=.venv/bin/python
UVICORN=.venv/bin/uvicorn

.PHONY: venv install migrate migrate-local run test ingest-all

venv:
	python3 -m venv .venv

install: venv
	$(PYTHON) -m pip install -r requirements.txt

migrate:
	$(PYTHON) -m alembic upgrade head

migrate-local:
	DATABASE_URL=postgresql+psycopg2://finops:finops123@127.0.0.1:5432/finops $(PYTHON) -m alembic upgrade head

run:
	$(UVICORN) finops_api.main:app --reload --port 8000

test:
	$(PYTHON) -m pytest -q

ingest-all:
	$(PYTHON) -m finops_api.jobs.ingest_cli providers --provider all
