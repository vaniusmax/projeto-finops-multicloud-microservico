# FinOps Stack (Traefik + DB + Backend + Frontend)

Esta pasta agora possui 3 stacks Docker Compose:

- `docker-compose.yml`: infraestrutura base (Traefik, Postgres, pgAdmin, Portainer)
- `docker-compose.backend.yml`: API FastAPI (`finops-api`)
- `docker-compose.frontend.yml`: app Next.js (`finops-web`)

## Pré-requisitos

- Docker + Docker Compose v2
- OpenSSL (para gerar certificado local)

## Hosts locais

Adicione no seu `/etc/hosts`:

```txt
127.0.0.1 finops.local
```

## 1) Gerar certificado local (opcional)

```bash
make cert
```

## 2) Subir stack base (Traefik + DB + utilitários)

```bash
make up
```

URLs:

- Traefik Dashboard: `http://finops.local/traefik/dashboard/`
- Portainer: `http://finops.local/portainer`
- pgAdmin: `http://finops.local/pgadmin`
- Postgres: `localhost:5432`

Credenciais padrão do Postgres:

- DB: `finops`
- User: `finops`
- Pass: `finops123`

## 3) Configurar backend e frontend

```bash
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
```

Ajuste principalmente:

- `.env.backend`: `DATABASE_URL`, `FINOPS_API_HOST`, `CORS_ORIGINS`, `AUTH_FRONTEND_BASE_URL`
- `.env.frontend`: `FINOPS_WEB_HOST`, `NEXT_PUBLIC_API_GATEWAY_URL`

## 4) Subir as stacks da aplicação

```bash
make backend-up
make frontend-up
```

Ou subir as duas:

```bash
make app-up
```

URLs:

- API Health: `http://finops.local/api/v1/health`
- Frontend: `http://finops.local`

## Deploy no servidor remoto (Docker Hub)

Fluxo recomendado para produção: usar imagens publicadas no Docker Hub.

### 1) Preparar DNS e firewall

- Aponte o host para o IP público do servidor:
  - `finops.seudominio.com` -> frontend, backend e endpoints auxiliares por path
- Libere portas de entrada no servidor/security group:
  - `22` (SSH)
  - `80` e `443` (Traefik)
- Restrinja `5432` (Postgres) para IPs confiáveis ou mantenha fechado publicamente.

### 2) Copiar a stack para o servidor

No seu computador local:

```bash
scp -i finops-dash-key.pem -o StrictHostKeyChecking=accept-new -r finops-traefik-stack ubuntu@SEU_IP:~/
```

### 3) Acessar servidor e configurar variáveis

```bash
ssh -i finops-dash-key.pem ubuntu@SEU_IP
cd ~/finops-traefik-stack
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
printf "FINOPS_BASE_HOST=finops.seudominio.com\n" > .env
```

Edite os arquivos:

- `.env`
  - `FINOPS_BASE_HOST=finops.seudominio.com`
- `.env.backend`
  - `BACKEND_IMAGE=vaniusoliveira/finops-backend:latest`
  - `FINOPS_API_HOST=finops.seudominio.com`
  - `CORS_ORIGINS=https://finops.seudominio.com`
  - `AUTH_FRONTEND_BASE_URL=https://finops.seudominio.com`
  - `DATABASE_URL=postgresql+psycopg2://...`
- `.env.frontend`
  - `FRONTEND_IMAGE=vaniusoliveira/finops-frontend:latest`
  - `FINOPS_WEB_HOST=finops.seudominio.com`
  - `NEXT_PUBLIC_API_GATEWAY_URL=https://finops.seudominio.com`

### 4) Subir stack base

```bash
make up
```

### 5) Deploy da aplicação direto do Docker Hub

```bash
make hub-deploy
```

Esse comando faz `pull` das imagens e recria `finops-api` e `finops-web` com `--no-build`.

### 6) Validar deploy

```bash
make app-status
curl -fsS https://finops.seudominio.com/api/v1/health
```

### 7) Atualizar versões publicadas

Sempre que subir uma nova imagem no Docker Hub:

```bash
make hub-deploy
```

## Comandos úteis

```bash
make status            # stack base
make backend-status    # stack backend
make frontend-status   # stack frontend
make hub-deploy        # pull + deploy backend/frontend via Docker Hub
make psql              # acesso ao postgres
make reset             # recria stack base e reexecuta SQL init
```
