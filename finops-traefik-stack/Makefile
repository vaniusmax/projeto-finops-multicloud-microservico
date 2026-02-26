.PHONY: up down logs reset psql cert status sql-init

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
