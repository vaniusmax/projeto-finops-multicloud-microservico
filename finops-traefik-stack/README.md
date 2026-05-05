# FinOps Stack (Traefik + Postgres + Backend + Frontend)

Stack oficial de infraestrutura e deploy do FinOps Multicloud.

## Escopo desta pasta

- `docker-compose.yml`: compose unificado com profiles (`infra`, `init`, `migrate`, `backend`, `frontend`, `app`)
- `Makefile`: comandos operacionais da stack
- `scripts/001_finops_canonical_v0.sql`: bootstrap SQL inicial
- `scripts/002_finops_multi_tenant.sql`: upgrade SQL legada de multi-tenant
- `docker-compose.frontend.yml`: arquivo legado (não é o fluxo oficial atual)

## Fonte de verdade

- Operação de ambiente: `docker-compose.yml` + `Makefile` desta pasta
- Evolução de schema da aplicação: Alembic em `../finops-micro/backend/src/finops_api/db/migrations/versions`
- Deploy da aplicação: imagens Docker Hub (`vaniusoliveira/finops-backend`, `vaniusoliveira/finops-frontend`)

## Pré-requisitos

- Docker + Docker Compose v2
- OpenSSL (opcional para certificado local)

## Hosts (local x prod)

No `/etc/hosts`, use o padrao abaixo:

```txt
127.0.1.1 LNTB-ALG0387891
127.0.1.1 finops.local-dev traefik.local-dev pgadmin.local-dev portainer.local-dev
10.245.7.41 finops.local traefik.local pgadmin.local portainer.local
```

- `*.local-dev` representa a maquina local.
- `*.local` representa o ambiente de producao na AWS (`10.245.7.41`).

## Configuração de ambiente

```bash
cd finops-traefik-stack
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
```

Arquivos:

- `.env.backend`: imagem + variaveis da API e hosts de infra (`TRAEFIK_DASHBOARD_HOST`, `PGADMIN_HOST`, `PORTAINER_HOST`)
- `.env.frontend`: imagem + variaveis do frontend

## Fluxo local recomendado

### 1) (Opcional) certificado local

```bash
make cert
```

Se `mkcert` estiver instalado, `make cert` gera certificado confiavel pela CA local.

### 2) Subir infra base

```bash
make up
```

### 3) Inicializar schema canônico (primeira execução)

```bash
make sql-init
```

### 4) Aplicar migrations Alembic

```bash
make migrate
```

### 5) Subir aplicações

```bash
make app-up
```

Alternativa:

```bash
make backend-up
make frontend-up
```

## URLs locais

- Frontend: `http://finops.local-dev`
- API health: `http://finops.local-dev/api/v1/health`
- API docs (Swagger): `http://finops.local-dev/docs`
- API docs (ReDoc): `http://finops.local-dev/redoc`
- Traefik: `http://traefik.local-dev`
- pgAdmin: `http://pgadmin.local-dev`
- Portainer: `http://portainer.local-dev`

Credenciais padrão do Postgres (local):

- DB: `finops`
- User: `finops`
- Password: `finops123`

Observação: o Postgres não expõe mais `5432` no host. Use `make psql` para acesso local.

## Banco de dados

Comandos úteis:

```bash
make sql-init
make migrate
make psql
```

- `sql-init`: aplica schema canônico SQL (bootstrap inicial)
- `migrate`: executa `alembic upgrade head` em container isolado (`finops-api-migrate`)

## Credenciais de CLI para ingestão (produção)

O `finops-api` monta diretórios do host para leitura de credenciais:

- `/home/ubuntu/.aws -> /home/ubuntu/.aws:ro`
- `/home/ubuntu/.azure -> /home/ubuntu/.azure`
- `/home/ubuntu/.oci -> /home/ubuntu/.oci:ro`

Além disso, configure `.env.backend` (`AWS_*`, `AZURE_*`, `OCI_*`, `TENANT_CONFIGS_JSON`).

Validação rápida no container:

```bash
docker compose -f docker-compose.yml --env-file .env.backend --profile backend exec finops-api aws sts get-caller-identity
docker compose -f docker-compose.yml --env-file .env.backend --profile backend exec finops-api az account show
docker compose -f docker-compose.yml --env-file .env.backend --profile backend exec finops-api oci iam region list --profile DEFAULT
```

## Deploy via Docker Hub (produção)

### 1) Copiar stack para servidor

```bash
scp -i ~/.ssh/SEU_ARQUIVO_CHAVE.pem -o StrictHostKeyChecking=accept-new -r finops-traefik-stack ubuntu@SEU_IP:~/
```

### 2) Configurar variáveis no servidor

```bash
ssh -i ~/.ssh/SEU_ARQUIVO_CHAVE.pem ubuntu@SEU_IP
cd ~/finops-traefik-stack
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
```

Ajuste principalmente:

- `.env.backend`: `BACKEND_IMAGE`, `DATABASE_URL`, `FINOPS_API_HOST`, `CORS_ORIGINS`, `AUTH_FRONTEND_BASE_URL`
- `.env.frontend`: `FRONTEND_IMAGE`, `FINOPS_WEB_HOST`, `NEXT_PUBLIC_API_GATEWAY_URL`
- Para producao AWS, troque hosts `*.local-dev` para `*.local`.

Recomendação: use tags versionadas (`:vX.Y.Z`) em `BACKEND_IMAGE` e `FRONTEND_IMAGE`, evitando `latest`.

### 3) Subir infra base

```bash
make up
```

### 4) (Primeiro deploy) inicializar schema

```bash
make sql-init
```

### 5) Aplicar migrations

```bash
make migrate
```

### 6) Deploy das aplicações por imagem publicada

```bash
make hub-deploy
```

### 7) Validar

```bash
make app-status
curl -fsS http://finops.local/api/v1/health
```

## CI/CD (GitHub Actions)

Workflow: `.github/workflows/docker-build.yml`

- Trigger em push de tag `v*`
- Build/push de backend e frontend com cache GHA
- Build/push da imagem base (`finops-base-clls`) somente quando `Dockerfile.base-clls` muda

## Comandos operacionais

```bash
make status
make logs
make migrate
make backend-up
make backend-rebuild
make backend-logs
make frontend-up
make frontend-rebuild
make frontend-logs
make app-up
make app-status
make app-logs
make app-down
make reset
```

## Observações

- As migrations não rodam no `CMD` do backend; rodam no serviço isolado `finops-api-migrate`.
- `make hub-deploy` não executa migration automaticamente; execute `make migrate` antes do deploy.
- Evite versionar chaves privadas e arquivos de credenciais no repositório.
