.PHONY: up down logs reset psql cert status sql-init sql-upgrade-multi-tenant

cert:
	bash scripts/gen-cert.sh

up:
	docker compose up -d
	$(MAKE) sql-init

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

reset:
	docker compose down -v
	docker compose up -d
	$(MAKE) sql-init

psql:
	docker exec -it finops-db psql -U finops -d finops

status:
	docker compose ps

sql-init:
	docker compose --profile init run --rm finops-db-init

sql-upgrade-multi-tenant:
	docker compose run --rm -T finops-db-init bash -lc "psql -h finops-db -U finops -d finops -v ON_ERROR_STOP=1 -f /sql/002_finops_multi_tenant.sql"
