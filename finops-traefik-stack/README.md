# FinOps Stack (Traefik + Postgres + Backend + Frontend)

Stack oficial de infraestrutura e deploy para o FinOps Multicloud.

## Escopo desta pasta

- `docker-compose.yml`: base (Traefik, Postgres, pgAdmin, Portainer)
- `docker-compose.backend.yml`: API `finops-api`
- `docker-compose.frontend.yml`: web `finops-web`
- `Makefile`: comandos operacionais
- `scripts/001_finops_canonical_v0.sql`: bootstrap SQL da base
- `scripts/002_finops_multi_tenant.sql`: upgrade SQL multi-tenant

## Fonte de verdade

- Operação de ambiente: Compose/Makefile desta pasta
- Evolução de schema da aplicação: Alembic em `../finops-micro/backend/src/finops_api/db/migrations/versions`
- Deploy da aplicação: imagens Docker Hub (`vaniusoliveira/finops-backend`, `vaniusoliveira/finops-frontend`)

## Pré-requisitos

- Docker + Docker Compose v2
- OpenSSL (opcional para certificado local)

## Host local

Adicione no `/etc/hosts`:

```txt
127.0.0.1 finops.local
```

## Configuração de ambiente

```bash
cd finops-traefik-stack
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
printf "FINOPS_BASE_HOST=finops.local\n" > .env
```

Arquivos:

- `.env`: host base do Traefik (`FINOPS_BASE_HOST`)
- `.env.backend`: imagem e variáveis da API
- `.env.frontend`: imagem e variáveis do Next.js

## Subir ambiente local

### 1) (Opcional) certificado local

```bash
make cert
```

### 2) Subir base (Traefik + DB + utilitários)

```bash
make up
```

`make up` também executa `make sql-init` para aplicar `scripts/001_finops_canonical_v0.sql`.

### 3) Subir aplicações

```bash
make backend-up
make frontend-up
```

Ou:

```bash
make app-up
```

## URLs locais

- Frontend: `http://finops.local`
- API health: `http://finops.local/api/v1/health`
- Traefik: `http://finops.local/traefik/dashboard/`
- pgAdmin: `http://finops.local/pgadmin`
- Portainer: `http://finops.local/portainer`
- Postgres: `localhost:5432`

Credenciais padrão do Postgres (local):

- DB: `finops`
- User: `finops`
- Password: `finops123`

## Banco de dados

Comandos úteis:

```bash
make sql-init
make sql-upgrade-multi-tenant
make psql
```

- `sql-init`: aplica schema canônico inicial.
- `sql-upgrade-multi-tenant`: aplica ajustes de multi-tenant.

## Credenciais de CLI para ingestão (produção)

O `finops-api` monta diretórios do host para leitura de credenciais:

- `/home/ubuntu/.aws -> /home/ubuntu/.aws:ro`
- `/home/ubuntu/.azure -> /home/ubuntu/.azure`
- `/home/ubuntu/.oci -> /home/ubuntu/.oci:ro`

Além disso, use `.env.backend` para apontar perfis/paths (`AWS_PROFILE`, `AZURE_*`, `OCI_*`, `TENANT_CONFIGS_JSON`).

Validação rápida no container:

```bash
docker compose -f docker-compose.backend.yml --env-file .env.backend exec finops-api aws sts get-caller-identity
docker compose -f docker-compose.backend.yml --env-file .env.backend exec finops-api az account show
docker compose -f docker-compose.backend.yml --env-file .env.backend exec finops-api oci iam region list --profile DEFAULT
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
printf "FINOPS_BASE_HOST=finops.seudominio.com\n" > .env
```

Ajuste principalmente:

- `.env.backend`: `BACKEND_IMAGE`, `DATABASE_URL`, `FINOPS_API_HOST`, `CORS_ORIGINS`, `AUTH_FRONTEND_BASE_URL`
- `.env.frontend`: `FRONTEND_IMAGE`, `FINOPS_WEB_HOST`, `NEXT_PUBLIC_API_GATEWAY_URL`

### 3) Subir base

```bash
make up
```

### 4) Deploy das aplicações por imagem publicada

```bash
make hub-deploy
```

### 5) Validar

```bash
make app-status
curl -fsS https://finops.seudominio.com/api/v1/health
```

## Comandos operacionais

```bash
make status
make logs
make backend-status
make backend-logs
make frontend-status
make frontend-logs
make app-status
make app-logs
make app-down
make reset
```

## Observações

- O `backend` executa `alembic upgrade head` no start do container.
- Evite versionar chaves privadas e arquivos de credenciais no repositório.
