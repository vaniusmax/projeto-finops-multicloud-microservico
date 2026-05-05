# Documentação da API do Dashboard (Backend)

## 1. Visão geral

- **Aplicação:** `FinOps Micro API` (FastAPI)
- **Prefixo base da API v1:** `/api/v1`
- **Rota raiz da aplicação:** `/` (fora do prefixo `/api/v1`)
- **Formato padrão:** JSON
- **CORS:** configurável por `CORS_ORIGINS` e `CORS_ORIGIN_REGEX`

### 1.1 Tratamento global de erros

- `ValueError` não tratado no endpoint vira **HTTP 400** com `{"detail": "<mensagem>"}`.
- Exceções genéricas não tratadas viram **HTTP 500** com `{"detail": "Erro interno inesperado"}`.

### 1.2 Autenticação

- A API usa **Bearer token** somente nos endpoints:
  - `GET /api/v1/auth/me`
  - `POST /api/v1/auth/logout`
- Formato obrigatório do header:
  - `Authorization: Bearer <token>`
- Se o header estiver ausente/malformado, retorna **401**.

### 1.3 Convenções de filtros FinOps

Nos endpoints de analytics/cost explorer, os filtros mais comuns são:

- `cloud`: `aws | azure | oci | all` (default: `all`)
- `tenant_key`: opcional, mas pode se tornar obrigatório em cloud multi-tenant
- `from` e `to`: datas obrigatórias (`YYYY-MM-DD`)
- `currency`: `BRL | USD` (default: `BRL`)
- `services`: lista opcional de serviços
- `accounts`: lista opcional de contas

Regras importantes:

- `from` não pode ser maior que `to`
- o intervalo máximo é controlado por `INGEST_MAX_RANGE_DAYS` (default atual: `366`)
- quando `cloud` é multi-tenant e há mais de um tenant configurado, `tenant_key` é obrigatório

### 1.4 Ingestão automática e refresh

- Com `AUTO_INGEST_ON_REQUEST=true`, vários endpoints tentam preencher lacunas automaticamente via `AutoIngestService`.
- Alguns endpoints aceitam `refresh=true`:
  - força ingestão ativa via CLI (AWS/Azure/OCI) no período solicitado
  - sincroniza taxa USD/BRL após ingestão

### 1.5 Como usar o Swagger (Docs)

Com a aplicação em execução no stack com Traefik, a documentação interativa fica disponível em:

- `http://finops.local/docs` (Swagger UI)
- `http://finops.local/redoc` (ReDoc)
- `http://finops.local/openapi.json` (especificação OpenAPI)

Se a porta `8000` do backend estiver publicada diretamente no host, também é possível acessar via IP da instância:

- `http://10.245.7.41:8000/docs`
- `http://10.245.7.41:8000/redoc`
- `http://10.245.7.41:8000/openapi.json`

#### Passo a passo rápido

1. Suba o backend:
   ```bash
   cd finops-micro/backend
   uv run uvicorn finops_api.main:app --reload --port 8000
   ```
2. Abra `http://finops.local/docs`.
3. Escolha o endpoint desejado.
4. Clique em **Try it out**.
5. Preencha query/body/header conforme o contrato.
6. Clique em **Execute** para enviar a requisição e ver request/response.

#### Testando endpoints autenticados no Swagger

Os endpoints `GET /api/v1/auth/me` e `POST /api/v1/auth/logout` exigem header `Authorization`.
No Swagger dessa API, esse header aparece como campo de parâmetro (não como botão global de autorização).

Fluxo recomendado:

1. Execute `POST /api/v1/auth/login` e copie o `accessToken`.
2. No endpoint autenticado (`/auth/me` ou `/auth/logout`), clique em **Try it out**.
3. Preencha o campo `authorization` com:
   ```text
   Bearer <seu_accessToken>
   ```
4. Execute e valide o retorno.

## 2. Endpoints

## 2.1 Base da aplicação

### `GET /`

**Função**
- Endpoint informativo da aplicação (nome e versão lógica da API).

**Entrada**
- Sem parâmetros.

**Resposta de sucesso (200)**
```json
{
  "name": "FinOps Micro API",
  "version": "v1"
}
```

---

## 2.2 Health

### `GET /api/v1/health`

**Função**
- Healthcheck simples para disponibilidade do backend.

**Entrada**
- Sem parâmetros.

**Resposta de sucesso (200)**
```json
{
  "status": "ok"
}
```

---

## 2.3 Auth

### `POST /api/v1/auth/register`

**Função**
- Inicia cadastro de usuário do dashboard e dispara e-mail de verificação.

**Body**
```json
{
  "first_name": "string (2..128)",
  "last_name": "string (2..128)",
  "email": "string (6..320)"
}
```

**Regras e comportamento**
- Normaliza e-mail para minúsculo.
- Valida domínio permitido (`AUTH_ALLOWED_EMAIL_DOMAINS`).
- Se usuário já existe e está verificado: erro.
- Se usuário não existe: cria registro pendente.
- Gera token de verificação, invalida tokens pendentes anteriores e envia e-mail.

**Resposta de sucesso (200)**
```json
{
  "status": "pending_verification",
  "email": "usuario@dominio.com",
  "message": "Enviamos um e-mail para concluir seu cadastro no dashboard."
}
```

**Erros comuns**
- `400`: domínio não permitido, usuário já cadastrado/validado, dados inválidos.

### `POST /api/v1/auth/verify-email`

**Função**
- Conclui cadastro: valida token de e-mail, define senha e cria sessão autenticada.

**Body**
```json
{
  "token": "string (min 16)",
  "password": "string (8..128)"
}
```

**Regras e comportamento**
- Token é validado por hash (`sha256`) no banco.
- Token deve existir, não estar consumido e não estar expirado.
- Usuário deve estar ativo.
- Marca e-mail como verificado, grava hash de senha (PBKDF2) e gera sessão.

**Resposta de sucesso (200)**
```json
{
  "accessToken": "token",
  "expiresAt": "datetime",
  "user": {
    "userId": "uuid",
    "firstName": "Nome",
    "lastName": "Sobrenome",
    "email": "usuario@dominio.com",
    "isEmailVerified": true
  }
}
```

**Erros comuns**
- `400`: token inválido/expirado/já usado, senha curta, usuário inativo.

### `POST /api/v1/auth/login`

**Função**
- Autentica usuário existente e cria sessão de acesso.

**Body**
```json
{
  "email": "string (6..320)",
  "password": "string (8..128)"
}
```

**Regras e comportamento**
- Exige usuário ativo, e-mail verificado e senha correta.
- Cria sessão com expiração baseada em `AUTH_SESSION_TTL_HOURS`.

**Resposta de sucesso (200)**
- Mesmo contrato de `AuthSessionResponse` do endpoint de verificação de e-mail.

**Erros comuns**
- `400`: credenciais inválidas, e-mail não verificado.

### `GET /api/v1/auth/me`

**Função**
- Retorna os dados do usuário autenticado pela sessão atual.

**Headers**
- `Authorization: Bearer <accessToken>`

**Regras e comportamento**
- Token deve existir e estar no formato Bearer.
- Sessão deve existir, não revogada e não expirada.
- Atualiza `last_seen_at` da sessão.

**Resposta de sucesso (200)**
```json
{
  "userId": "uuid",
  "firstName": "Nome",
  "lastName": "Sobrenome",
  "email": "usuario@dominio.com",
  "isEmailVerified": true
}
```

**Erros comuns**
- `401`: header ausente/malformado, sessão inválida/expirada, usuário inativo.

### `POST /api/v1/auth/logout`

**Função**
- Revoga a sessão associada ao token informado.

**Headers**
- `Authorization: Bearer <accessToken>`

**Regras e comportamento**
- Se token existir, sessão recebe `revoked_at`.
- Se token não existir, endpoint ainda retorna sucesso lógico.

**Resposta de sucesso (200)**
```json
{
  "status": "ok"
}
```

**Erros comuns**
- `401`: header ausente ou malformado.

---

## 2.4 Cloud

### `GET /api/v1/cloud/{cloud}/tenants`

**Função**
- Lista tenants ativos disponíveis para uma cloud específica.

**Path params**
- `cloud`: `aws | azure | oci`

**Regras e comportamento**
- Valida `cloud` (fora do conjunto aceito retorna 400).
- Sincroniza tenants configurados (`TENANT_CONFIGS_JSON`, `AWS_TENANTS`, `AZURE_TENANTS`, `OCI_TENANTS`) para a tabela de dimensão.
- Retorna somente tenants ativos e compatíveis com configuração runtime.

**Resposta de sucesso (200)**
```json
[
  {
    "tenantKey": "tenant-a",
    "tenantName": "Tenant A",
    "cloud": "aws"
  }
]
```

**Erros comuns**
- `400`: cloud inválida.

---

## 2.5 FinOps

### `GET /api/v1/finops/summary`

**Função**
- Retorna KPIs principais do dashboard para o período:
  - total do período (`totalWeek`)
  - variação percentual vs período anterior (`deltaWeek`)
  - média diária
  - dia de pico
  - acumulados do mês e ano até `to`
  - metas (`budgetMonth`, `budgetYear`)
  - taxa USD/BRL (`usdRate`)

**Query params**
- `cloud`, `tenant_key`, `from`, `to`, `currency`, `services`, `accounts`
- `refresh` (bool, default `false`)

**Regras e comportamento**
- Faz resolução de tenant e aplica filtros.
- Com `refresh=true`: reingere dados do início do ano até `to`.
- Com `refresh=false`: tenta auto-ingest incremental no mesmo intervalo YTD.
- Sincroniza cotação USD/BRL.
- Tolerante a cobertura parcial de dados (registra warning; não interrompe com 409).

**Resposta de sucesso (200)**
- `SummaryV2Response`.

**Erros comuns**
- `400`: filtros inválidos (datas, moeda, tenant, etc.).
- `500`: falhas não tratadas em ingestão/integrações.

### `GET /api/v1/finops/daily`

**Função**
- Série diária do período com total por dia e breakdown por serviço (`byService`) limitado por `topN`.

**Query params**
- Filtros padrão FinOps
- `topN` (1..50, default `10`)
- `refresh` (bool)

**Regras e comportamento**
- Garante ingestão automática ou refresh explícito no intervalo solicitado.
- Em cenários com muitos serviços, pode consolidar excedente em `Others`.

**Resposta de sucesso (200)**
- Lista de `DailyItem`.

**Erros comuns**
- `400`: filtros inválidos.
- `500`: erro de ingestão/runtime não capturado como `ValueError`.

### `GET /api/v1/finops/top-services`

**Função**
- Ranking de serviços por custo no período com:
  - total
  - participação (`sharePct`)
  - delta absoluto e percentual vs período anterior de mesmo tamanho

**Query params**
- Filtros padrão FinOps
- `topN` (1..50)
- `refresh` (bool)

**Regras e comportamento**
- Usa breakdown diário para montar total por serviço.
- Pode incluir item `Others` para consolidar cauda.

**Resposta de sucesso (200)**
- Lista de `RankedItemV2` (`serviceName`, `total`, `sharePct`, `delta`, `deltaPct`).

**Erros comuns**
- `400`: filtros inválidos.

### `GET /api/v1/finops/top-accounts`

**Função**
- Ranking de contas/escopos por custo com métricas de participação e variação vs período anterior.

**Query params**
- Filtros padrão FinOps
- `topN` (1..50)
- `refresh` (bool)

**Regras e comportamento**
- Para AWS, usa visão de conta apropriada para evitar mistura indevida com fontes de serviço.
- Resolve nomes de conta AWS via mapeamento configurável (`AWS_ACCOUNT_NAMES_JSON`) quando disponível.

**Resposta de sucesso (200)**
- Lista de `RankedItemV2` (`linkedAccount`, `total`, `sharePct`, `delta`, `deltaPct`).

**Erros comuns**
- `400`: filtros inválidos.

### `GET /api/v1/finops/filters`

**Função**
- Fornece listas de opções para filtros de UI:
  - serviços
  - contas

**Query params**
- `cloud` (`aws|azure|oci|all`)
- `tenant_key` (opcional)
- `month` (opcional, formato `YYYY-MM`)

**Regras e comportamento**
- Retorna top itens (até 50) ordenados por custo.
- Se `month` for informado, restringe a janela ao mês.
- Não força refresh/ingest neste endpoint.

**Resposta de sucesso (200)**
```json
{
  "services": ["Compute", "Storage"],
  "accounts": ["Conta A", "Conta B"]
}
```

**Erros comuns**
- `400`: mês inválido, tenant inválido ou filtros inconsistentes.

### `POST /api/v1/finops/ai/insights`

**Função**
- Gera resposta analítica em linguagem natural para perguntas do dashboard.

**Body (`AiInsightRequest`)**
- `cloud`, `tenant_key`, `from`, `to`, `currency`
- `topN` (1..50)
- `services`, `accounts` (opcionais)
- `question` (1..4000)
- `history` (até 8 mensagens úteis consideradas)
- `filters` (fallback para listas de `services/accounts`)

**Regras e comportamento**
- Exige `question` não vazia.
- Resolve tenant e tenta auto-ingest do período.
- Verifica disponibilidade de dados; com cobertura parcial registra warning e segue.
- Pipeline de geração:
  - 1) tentativa MCP estruturada para perguntas de comparação SQL/multi-cloud
  - 2) tentativa LLM (`OPENAI_MODEL`)
  - 3) fallback heurístico determinístico

**Resposta de sucesso (200)**
```json
{
  "answerMarkdown": "texto",
  "highlights": ["..."],
  "suggestedActions": ["..."]
}
```

**Erros comuns**
- `400`: payload inválido, pergunta vazia, filtros inválidos.
- `500`: falhas inesperadas de integração.

### `POST /api/v1/finops/analytics/insights`

**Função**
- Gera resumo executivo de insights analíticos (drivers, riscos, ações e perguntas sugeridas).

**Body (`AnalyticsInsightRequest`)**
- `cloud`, `tenant_key`, `from`, `to`, `currency`, `topN`, `services`, `accounts`

**Regras e comportamento**
- Monta evidências a partir de summary + top services + top accounts + diário.
- Tenta LLM e, em caso de indisponibilidade/erro, usa fallback heurístico.

**Resposta de sucesso (200)**
- `AnalyticsInsightResponse` (`mode`, `summary`, `drivers`, `risks`, `actions`, `suggestedQuestions`, `evidence`).

**Erros comuns**
- `400`: filtros inválidos.

### `GET /api/v1/finops/cost-explorer/snapshot`

**Função**
- Retorna snapshot de KPIs do Cost Explorer:
  - total do período
  - variação percentual
  - concentração top1/top3
  - pico diário
  - maior serviço e maior conta

**Query params**
- Filtros padrão FinOps
- `topN` (1..50)
- `refresh` (bool)

**Regras e comportamento**
- Usa o mesmo fluxo de ingestão/sincronização de `summary` (incluindo janela anual).

**Resposta de sucesso (200)**
- `CostExplorerSnapshotResponse`.

### `GET /api/v1/finops/cost-explorer/breakdown`

**Função**
- Lista composição do custo por dimensão (`service` ou `account`) com métricas de contribuição.

**Query params**
- Filtros padrão FinOps
- `groupBy`: `service | account` (default `service`)
- `topN` (1..50)
- `refresh` (bool)

**Regras e comportamento**
- `contributionPct` mede contribuição relativa entre itens com delta positivo.

**Resposta de sucesso (200)**
- Lista de `CostExplorerBreakdownItem`.

### `GET /api/v1/finops/cost-explorer/trend`

**Função**
- Série temporal para análise de foco:
  - `selected`: custo do item selecionado (ou top itens)
  - `others`: restante
  - `total`: soma diária

**Query params**
- Filtros padrão FinOps
- `groupBy`: `service | account`
- `selectedItem` (opcional)
- `topN` (1..50)
- `refresh` (bool)

**Regras e comportamento**
- Se `selectedItem` não for enviado, usa os principais itens do breakdown.
- Internamente limita foco a no máximo 5 itens para manter legibilidade analítica.

**Resposta de sucesso (200)**
- Lista de `CostExplorerTrendItem`.

### `POST /api/v1/finops/cost-explorer/insights`

**Função**
- Gera narrativa investigativa do Cost Explorer com próximos drilldowns recomendados.

**Body (`CostExplorerInsightRequest`)**
- `cloud`, `tenant_key`, `from`, `to`, `currency`
- `topN`
- `groupBy` (`service|account`)
- `selectedItem` (opcional)
- `services`, `accounts` (opcionais)

**Regras e comportamento**
- Executa auto-ingest no período antes de gerar o insight.
- Tenta LLM; se indisponível, usa heurística.
- Retorna `nextDrilldowns` para orientar navegação analítica.

**Resposta de sucesso (200)**
- `CostExplorerInsightResponse`.

### `POST /api/v1/finops/reingest`

**Função**
- Reprocessa explicitamente ingestão do período para uma cloud ou para todas.

**Body**
```json
{
  "cloud": "aws|azure|oci|all",
  "tenant_key": "opcional",
  "from": "YYYY-MM-DD",
  "to": "YYYY-MM-DD"
}
```

**Regras e comportamento**
- Valida:
  - `from <= to`
  - intervalo dentro do limite configurado
  - cloud válida
- Para `cloud=all`, executa ingestão para `aws`, `azure` e `oci`.
- Quando aplicável, expande para múltiplos tenants configurados.
- Após ingestão, sincroniza taxa USD/BRL para a data `to`.

**Resposta de sucesso (200)**
```json
{
  "results": [
    {
      "provider": "aws",
      "rows_received": 100,
      "rows_written": 100
    }
  ]
}
```

**Erros comuns**
- `400`: cloud inválida, datas inválidas, tenant inválido, intervalo acima do limite.
- `409`: conflito operacional de ingestão (`RuntimeError`).

---

## 3. Observações operacionais importantes

- A maioria dos endpoints FinOps **não exige autenticação** no estado atual do código.
- `currency=BRL` pode usar:
  - `amount_brl` já persistido
  - conversão de `amount` em USD com taxa mais recente/fallback
- Para AWS, há separação de fontes para evitar mistura de visões de serviço e conta:
  - serviço: `aws_ce_service_cli`
  - conta: `aws_ce_account_cli`
- Endpoints de insight (`ai/insights`, `analytics/insights`, `cost-explorer/insights`) podem operar em modo:
  - `llm` (quando OpenAI disponível)
  - `heuristic` (fallback determinístico)
