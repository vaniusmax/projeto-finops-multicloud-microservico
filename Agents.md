# Infraestrutura Docker — Análise e Plano de Melhoria

## Contexto

O projeto FinOps Multicloud usa Docker Compose como orquestrador local e em produção, com Traefik como gateway único, PostgreSQL 16, backend FastAPI e frontend Next.js 14. A análise abaixo identifica os pontos críticos e propõe melhorias em três fases progressivas.

---

## O que funciona bem

- Redes separadas (`proxy` / `internal`) com isolamento correto
- Healthchecks em todos os serviços críticos
- Usuários não-root no backend (`app`) e frontend (`nextjs`)
- Multi-stage build no frontend (`deps → builder → runner`)
- Traefik com auto-discovery por labels — sem nginx.conf para manter
- Makefile cobrindo os cenários principais de operação
- Defaults sensatos nas variáveis de ambiente

---

## Problemas identificados

### Crítico

**1. AWS CLI, Azure CLI e OCI CLI instalados via `curl | bash` no `Dockerfile.prod`**

Cada build baixa ~600-800 MB da internet sem verificação de integridade. Uma interceptação de rede compromete o container inteiro. O build não é reproduzível (a URL pode mudar o binário sem aviso).

**2. Migrations Alembic rodando no `CMD` do container**

Se dois containers sobem simultaneamente (restart automático + deploy), dois processos tentam fazer `migrate` ao mesmo tempo — risco de deadlock ou corrompimento de estado. Migration precisa ser um job isolado, não parte do start da aplicação.

**3. Estratégia dual de migrations (SQL scripts + Alembic)**

O `finops-db-init` roda scripts SQL (`001_*.sql`, `002_*.sql`), e o backend também roda `alembic upgrade head`. Dois sistemas gerenciando o mesmo schema em paralelo vão desincronizar em produção.

### Alto

**4. Credenciais cloud montadas diretamente do host**

```yaml
volumes:
  - /home/ubuntu/.aws:/home/ubuntu/.aws:ro
  - /home/ubuntu/.azure:/home/ubuntu/.azure     # read-write!
  - /home/ubuntu/.oci:/home/ubuntu/.oci:ro
```

O container tem acesso às credenciais do usuário `ubuntu` da VM inteira. Azure é montado com escrita.

**5. PostgreSQL com porta exposta e senha hardcoded**

```yaml
ports:
  - "5432:5432"           # exposto ao host/rede local
environment:
  POSTGRES_PASSWORD: finops123   # hardcoded
```

Em produção, `5432` não deve ser acessível fora da rede `internal`.

**6. Tags `latest` em imagens críticas**

```yaml
image: portainer/portainer-ce:latest
image: vaniusoliveira/finops-backend:latest
```

`latest` é não-reproduzível: um `docker compose pull` pode trazer uma versão quebrada silenciosamente.

### Médio

**7. `make backend-up` e `make frontend-up` sempre reconstroem a imagem**

O flag `--build` em todo `up` recompila localmente mesmo quando o deploy deveria usar a imagem do Docker Hub.

**8. `make up` chama `sql-init` automaticamente a cada execução**

Se o banco já existe, o script SQL pode falhar ou aplicar migração duplicada.

**9. ~40 variáveis de ambiente inline no `docker-compose.backend.yml`**

Com `env_file:` o arquivo ficaria 10x menor com o mesmo resultado.

**10. Frontend sem diretório `public/` copiado no runner stage**

Se assets estáticos forem adicionados a `public/` no futuro, o container de produção não os servirá.

**11. Backend usa `requirements.txt` mas o projeto tem `pyproject.toml` com `uv.lock`**

Dois sistemas de dependências. O `uv` é 10-100x mais rápido que pip e o lockfile já existe.

**12. Sem `.dockerignore`** em backend e frontend — o build context inclui `node_modules`, `__pycache__`, `.git`, etc.

---

## Plano de Melhoria

### Fase 1 — Correções imediatas ✅ Implementado

| # | Ação | Arquivo(s) |
|---|------|------------|
| 1a | Criar `.dockerignore` no backend | `finops-micro/backend/.dockerignore` |
| 1b | Criar `.dockerignore` no frontend | `finops-micro/frontend/.dockerignore` |
| 1c | Preparar cópia de `public/` no Dockerfile do frontend | `finops-micro/frontend/Dockerfile.prod` |
| 1d | Separar migrations do `CMD` — service `finops-api-migrate` com profile | `Dockerfile.prod`, `docker-compose.backend.yml` |
| 1e | Remover `--build` do `make backend-up` e `make frontend-up`; criar `make backend-rebuild` e `make frontend-rebuild`; adicionar `make migrate` | `Makefile` |

### Fase 2 — Segurança e reprodutibilidade ✅ Implementado

| # | Ação | Arquivo(s) |
|---|------|------------|
| 2a | Criar `Dockerfile.base-clls` com CLIs pré-instaladas (imagem base versionada) | `finops-micro/backend/Dockerfile.base-clls` |
| 2b | Atualizar `Dockerfile.prod` para usar imagem base e `uv` com `uv.lock` | `finops-micro/backend/Dockerfile.prod` |
| 2c | Pinar todas as tags de imagem nos docker-compose | `docker-compose.yml`, `docker-compose.backend.yml`, `docker-compose.frontend.yml` |
| 2d | Remover porta `5432` exposta do `docker-compose.yml` (acessível via `make psql`) | `docker-compose.yml` |

### Fase 3 — CI/CD e automação ✅ Implementado

| # | Ação | Arquivo(s) |
|---|------|------------|
| 3a | GitHub Actions para build e push versionado (trigger em tag `v*`, cache GHA) | `.github/workflows/docker-build.yml` |
| 3b | Job dedicado para `finops-base-clls` — só constrói quando `Dockerfile.base-clls` mudar | `.github/workflows/docker-build.yml` |
| 3c | Compose unificado com profiles `infra`, `migrate`, `backend`, `frontend`, `app` | `finops-traefik-stack/docker-compose.yml` (removidos `docker-compose.backend.yml` e `docker-compose.frontend.yml`) |
| 3d | Next.js standalone output — imagem frontend ~150 MB (era ~500 MB) | `finops-micro/frontend/next.config.js`, `finops-micro/frontend/Dockerfile.prod` |
| 3e | Resource limits em todos os serviços (`cpus` + `memory`) | `finops-traefik-stack/docker-compose.yml` |
| 3f | Secrets injetados via GitHub Actions (`secrets.DOCKERHUB_*`, `vars.API_GATEWAY_URL`) | `.github/workflows/docker-build.yml` |

---

## Fluxo de build recomendado (após Fase 3)

```
git push v1.2.0
       │
       ▼
GitHub Actions
  ├── [se Dockerfile.base-clls mudou]
  │     └── build + push finops-base-clls:1.2.0
  │
  ├── build backend → vaniusoliveira/finops-backend:1.2.0
  └── build frontend → vaniusoliveira/finops-frontend:1.2.0
       │
       ▼
make hub-deploy IMAGE_TAG=1.2.0
  ├── docker compose pull finops-api  (baixa :1.2.0)
  ├── make migrate                    (alembic upgrade head, isolado)
  └── docker compose up -d --no-build --force-recreate
```

---

## Comandos Makefile após Fase 1 e 2

| Comando | O que faz |
|---------|----------|
| `make up` | Sobe infra base (Traefik, PostgreSQL, pgAdmin, Portainer) |
| `make migrate` | Roda `alembic upgrade head` em container isolado |
| `make backend-up` | Sobe a API usando imagem existente (sem rebuild) |
| `make backend-rebuild` | Reconstrói a imagem da API localmente e sobe |
| `make frontend-up` | Sobe o frontend usando imagem existente (sem rebuild) |
| `make frontend-rebuild` | Reconstrói a imagem do frontend localmente e sobe |
| `make app-up` | Sobe backend + frontend (sem rebuild) |
| `make hub-build` | Build local para Docker Hub (backend + frontend) |
| `make hub-deploy` | Pull do Docker Hub e recria containers |
| `make base-build` | Build da imagem base com CLIs (necessário antes do hub-build) |
| `make base-push` | Push da imagem base para Docker Hub |
| `make psql` | Shell psql direto no container do banco |
| `make logs` | Logs da infra base |
| `make backend-logs` | Logs da API |
| `make frontend-logs` | Logs do frontend |
