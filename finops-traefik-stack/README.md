# FinOps Stack (Traefik + Postgres + pgAdmin + Portainer)

Este pacote sobe:
- Traefik (reverse proxy) em 80/443
- Postgres (tambem exposto na porta 5432 para acesso local)
- pgAdmin via Traefik
- Portainer via Traefik

## Pré-requisitos
- Docker + Docker Compose v2
- OpenSSL (para gerar certificado local)

## 1) Gerar certificado (self-signed)
```bash
make cert
```

## 2) Subir o stack
```bash
make up
```

## URLs (local)
- Traefik Dashboard: https://traefik.localhost
- Portainer: https://portainer.localhost
- pgAdmin: https://pgadmin.localhost

> O browser vai alertar por ser certificado self-signed. É esperado.

## Postgres
O Postgres esta acessivel na rede docker `internal` e no host em `localhost:5432`.
Credenciais:
- DB: finops
- User: finops
- Pass: finops123

## Entrar no psql
```bash
make psql
```

## Schema do banco
Coloque o seu SQL em:
`db/init/001_finops_canonical_v0.sql`

Os arquivos dentro de `db/init/` são executados automaticamente somente na primeira criação do volume.
Para resetar:
```bash
make reset
```
