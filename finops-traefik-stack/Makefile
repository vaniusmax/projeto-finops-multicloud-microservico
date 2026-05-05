COMPOSE := docker-compose.yml

BACKEND_ENV  ?= .env.backend
FRONTEND_ENV ?= .env.frontend

DOCKER_HUB_NAMESPACE ?= vaniusoliveira
BACKEND_HUB_IMAGE    ?= $(DOCKER_HUB_NAMESPACE)/finops-backend
FRONTEND_HUB_IMAGE   ?= $(DOCKER_HUB_NAMESPACE)/finops-frontend
BASE_CLLS_IMAGE      ?= $(DOCKER_HUB_NAMESPACE)/finops-base-clls
IMAGE_TAG            ?= latest

.PHONY: up down logs reset psql cert status sql-init \
	migrate \
	backend-up backend-rebuild backend-down backend-logs backend-status \
	frontend-up frontend-rebuild frontend-down frontend-logs frontend-status \
	app-up app-down app-logs app-status \
	base-build base-push \
	backend-build-hub frontend-build-hub hub-build hub-deploy

# ── Infraestrutura base ────────────────────────────────────────────────────────

cert:
	bash scripts/gen-cert.sh

up:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile infra up -d

down:
	docker compose -f $(COMPOSE) --profile infra down

logs:
	docker compose -f $(COMPOSE) --profile infra logs -f --tail=200

reset:
	docker compose -f $(COMPOSE) --profile infra down -v
	$(MAKE) up

status:
	docker compose -f $(COMPOSE) --profile infra ps

psql:
	docker exec -it finops-db psql -U finops -d finops

sql-init:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile infra --profile init run --rm finops-db-init

# ── Migrations ────────────────────────────────────────────────────────────────

migrate:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile migrate run --rm finops-api-migrate

# ── Backend ───────────────────────────────────────────────────────────────────

backend-up:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile backend up -d

backend-rebuild:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile backend up -d --build

backend-down:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile backend down

backend-logs:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile backend logs -f --tail=200

backend-status:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile backend ps

# ── Frontend ──────────────────────────────────────────────────────────────────

frontend-up:
	docker compose -f $(COMPOSE) --env-file $(FRONTEND_ENV) --profile frontend up -d

frontend-rebuild:
	docker compose -f $(COMPOSE) --env-file $(FRONTEND_ENV) --profile frontend up -d --build

frontend-down:
	docker compose -f $(COMPOSE) --env-file $(FRONTEND_ENV) --profile frontend down

frontend-logs:
	docker compose -f $(COMPOSE) --env-file $(FRONTEND_ENV) --profile frontend logs -f --tail=200

frontend-status:
	docker compose -f $(COMPOSE) --env-file $(FRONTEND_ENV) --profile frontend ps

# ── App (backend + frontend) ──────────────────────────────────────────────────

app-up:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --env-file $(FRONTEND_ENV) --profile app up -d

app-down:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --env-file $(FRONTEND_ENV) --profile app down

app-logs:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --env-file $(FRONTEND_ENV) --profile app logs -f --tail=200

app-status:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --env-file $(FRONTEND_ENV) --profile app ps

# ── Imagem base com CLIs ──────────────────────────────────────────────────────

base-build:
	docker build \
		--build-arg TARGETARCH=$(shell dpkg --print-architecture 2>/dev/null || echo amd64) \
		-t $(BASE_CLLS_IMAGE):$(IMAGE_TAG) \
		-f ../finops-micro/backend/Dockerfile.base-clls \
		../finops-micro/backend

base-push:
	docker push $(BASE_CLLS_IMAGE):$(IMAGE_TAG)

# ── Docker Hub ────────────────────────────────────────────────────────────────

backend-build-hub:
	docker build \
		-t $(BACKEND_HUB_IMAGE):$(IMAGE_TAG) \
		-f ../finops-micro/backend/Dockerfile.prod \
		../finops-micro/backend

frontend-build-hub:
	@set -a; \
	if [ -f "$(FRONTEND_ENV)" ]; then . "./$(FRONTEND_ENV)"; fi; \
	set +a; \
	docker build \
			--build-arg NEXT_PUBLIC_API_GATEWAY_URL="$${NEXT_PUBLIC_API_GATEWAY_URL:-http://finops.local-dev}" \
		--build-arg NEXT_PUBLIC_API_BASE_PATH="$${NEXT_PUBLIC_API_BASE_PATH:-/api/v1}" \
		--build-arg NEXT_PUBLIC_USE_MOCKS="$${NEXT_PUBLIC_USE_MOCKS:-false}" \
		-t $(FRONTEND_HUB_IMAGE):$(IMAGE_TAG) \
		-f ../finops-micro/frontend/Dockerfile.prod \
		../finops-micro/frontend

hub-build: backend-build-hub frontend-build-hub

hub-deploy:
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --profile backend pull finops-api
	docker compose -f $(COMPOSE) --env-file $(FRONTEND_ENV) --profile frontend pull finops-web
	docker compose -f $(COMPOSE) --env-file $(BACKEND_ENV) --env-file $(FRONTEND_ENV) --profile app up -d --no-build --force-recreate
