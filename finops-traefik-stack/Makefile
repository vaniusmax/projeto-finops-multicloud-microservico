BASE_COMPOSE := docker-compose.yml
BACKEND_COMPOSE := docker-compose.backend.yml
FRONTEND_COMPOSE := docker-compose.frontend.yml

BACKEND_ENV ?= .env.backend
FRONTEND_ENV ?= .env.frontend
DOCKER_HUB_NAMESPACE ?= vaniusoliveira
BACKEND_HUB_IMAGE ?= $(DOCKER_HUB_NAMESPACE)/finops-backend
FRONTEND_HUB_IMAGE ?= $(DOCKER_HUB_NAMESPACE)/finops-frontend
IMAGE_TAG ?= latest

.PHONY: up down logs reset psql cert status sql-init sql-upgrade-multi-tenant \
	backend-up backend-down backend-logs backend-status \
	frontend-up frontend-down frontend-logs frontend-status \
	app-up app-down app-logs app-status \
	backend-build-hub frontend-build-hub hub-build \
	backend-deploy-hub frontend-deploy-hub hub-deploy

cert:
	bash scripts/gen-cert.sh

up:
	docker compose -f $(BASE_COMPOSE) up -d
	$(MAKE) sql-init

down:
	docker compose -f $(BASE_COMPOSE) down

logs:
	docker compose -f $(BASE_COMPOSE) logs -f --tail=200

reset:
	docker compose -f $(BASE_COMPOSE) down -v
	docker compose -f $(BASE_COMPOSE) up -d
	$(MAKE) sql-init

psql:
	docker exec -it finops-db psql -U finops -d finops

status:
	docker compose -f $(BASE_COMPOSE) ps

sql-init:
	docker compose -f $(BASE_COMPOSE) --profile init run --rm finops-db-init

sql-upgrade-multi-tenant:
	docker compose -f $(BASE_COMPOSE) run --rm -T finops-db-init bash -lc "psql -h finops-db -U finops -d finops -v ON_ERROR_STOP=1 -f /sql/002_finops_multi_tenant.sql"

backend-up:
	docker compose -f $(BACKEND_COMPOSE) --env-file $(BACKEND_ENV) up -d --build

backend-down:
	docker compose -f $(BACKEND_COMPOSE) --env-file $(BACKEND_ENV) down

backend-logs:
	docker compose -f $(BACKEND_COMPOSE) --env-file $(BACKEND_ENV) logs -f --tail=200

backend-status:
	docker compose -f $(BACKEND_COMPOSE) --env-file $(BACKEND_ENV) ps

frontend-up:
	docker compose -f $(FRONTEND_COMPOSE) --env-file $(FRONTEND_ENV) up -d --build

frontend-down:
	docker compose -f $(FRONTEND_COMPOSE) --env-file $(FRONTEND_ENV) down

frontend-logs:
	docker compose -f $(FRONTEND_COMPOSE) --env-file $(FRONTEND_ENV) logs -f --tail=200

frontend-status:
	docker compose -f $(FRONTEND_COMPOSE) --env-file $(FRONTEND_ENV) ps

app-up: backend-up frontend-up

app-down:
	$(MAKE) frontend-down
	$(MAKE) backend-down

app-logs:
	docker compose -f $(BACKEND_COMPOSE) --env-file $(BACKEND_ENV) logs --tail=200
	docker compose -f $(FRONTEND_COMPOSE) --env-file $(FRONTEND_ENV) logs --tail=200

app-status:
	$(MAKE) backend-status
	$(MAKE) frontend-status

backend-build-hub:
	docker build -t $(BACKEND_HUB_IMAGE):$(IMAGE_TAG) -f ../finops-micro/backend/Dockerfile.prod ../finops-micro/backend

frontend-build-hub:
	@set -a; \
	if [ -f "$(FRONTEND_ENV)" ]; then . "./$(FRONTEND_ENV)"; fi; \
	set +a; \
	docker build \
		--build-arg NEXT_PUBLIC_API_GATEWAY_URL="$${NEXT_PUBLIC_API_GATEWAY_URL:-http://finops.local}" \
		--build-arg NEXT_PUBLIC_API_BASE_PATH="$${NEXT_PUBLIC_API_BASE_PATH:-/api/v1}" \
		--build-arg NEXT_PUBLIC_USE_MOCKS="$${NEXT_PUBLIC_USE_MOCKS:-false}" \
		-t $(FRONTEND_HUB_IMAGE):$(IMAGE_TAG) \
		-f ../finops-micro/frontend/Dockerfile.prod \
		../finops-micro/frontend

hub-build: backend-build-hub frontend-build-hub

backend-deploy-hub:
	docker compose -f $(BACKEND_COMPOSE) --env-file $(BACKEND_ENV) pull finops-api
	docker compose -f $(BACKEND_COMPOSE) --env-file $(BACKEND_ENV) up -d --no-build --force-recreate finops-api

frontend-deploy-hub:
	docker compose -f $(FRONTEND_COMPOSE) --env-file $(FRONTEND_ENV) pull finops-web
	docker compose -f $(FRONTEND_COMPOSE) --env-file $(FRONTEND_ENV) up -d --no-build --force-recreate finops-web

hub-deploy: backend-deploy-hub frontend-deploy-hub
