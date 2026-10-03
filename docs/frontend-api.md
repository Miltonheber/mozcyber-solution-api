# Mozcyber API — guia para o frontend

Base URL: `http://localhost:8000/api/v1/` (dev; frontend em `http://localhost:3000`) · Swagger interactivo: `/api/docs/` · schema: `/api/schema/`.
Formato: JSON. CORS aberto a todas as origens (a autenticação é por header, sem cookies).

> **Estado:** disponível — autenticação, classificação de mensagens, denúncias, reputação de números, moderação (blacklist/denúncias), **conteúdo educativo** (leitura pública + gestão) e **ocorrências de documentos perdidos** (esquadra/entidades).

## 1. Convenções

### Zonas pública e privada
| Zona | Autenticação | Rotas |
|---|---|---|
| Pública | Nenhuma (não enviar `Authorization`) | `public/*` |
| Privada | `Authorization: Bearer <access>` + permissão | tudo o resto |

As rotas públicas têm **limite de pedidos por IP** (ver §5).

### Erros
Todos os erros têm o mesmo formato:
```json
{ "code": "validation_error", "message": "Dados inválidos.", "details": { "phone": ["Número de telefone inválido."] } }
```
`details` é `null` quando não há detalhe. Em `validation_error`, `details` é um objecto `campo → [mensagens]`.

| Status | `code` | Quando |
|---|---|---|
| 400 | `validation_error` | corpo/parâmetros inválidos |
| 401 | `unauthorized` | token em falta/inválido/expirado |
| 403 | `permission_denied` | sem a permissão exigida |
| 404 | `not_found` | `id` inexistente |
| 429 | `throttled` | limite de pedidos excedido (header `Retry-After` em segundos) |

### Paginação (listagens privadas)
`?page=1&size=20` (size máx. 100). Resposta:
```json
{ "count": 42, "next": "…?page=2", "previous": null, "results": [ … ] }
```

### Filtros e pesquisa
Só os filtros listados em cada endpoint são aceites (exactos, via query string); outros são ignorados. `?search=` pesquisa nos campos indicados.

### Números de telefone
Pode enviar em qualquer formato razoável: `84 123 4567`, `841234567`, `+258 84-123-4567`, `00258841234567`. A API **normaliza para E.164** (`+258841234567`) e devolve sempre assim. Números locais de 9 dígitos assumem `+258`. Número inválido → 400.

### Valores enumerados
| Campo | Valores |
|---|---|
| `category` | `phishing`, `sim_swap`, `fake_prize`, `impersonation`, `loan_scam`, `other` |
| `status` (número) | `unknown`, `suspicious`, `blacklisted`, `cleared` |
| `verdict` | `safe`, `suspicious`, `fraud` |
| `channel` | `sms`, `call`, `whatsapp`, `email`, `other` |
| `status` (denúncia) | `pending`, `confirmed`, `rejected` |

Sugestão de UI: `blacklisted` → alerta vermelho; `suspicious` → aviso amarelo; `unknown`/`cleared` → neutro. `risk_score` (0–100) serve para barra/indicador.

---

## 2. Endpoints públicos

### 2.1 Classificar mensagem
`POST /api/v1/public/classify/` · throttle 20/min

Pedido:
```json
{ "phone": "84 123 4567", "message": "Parabéns, ganhou um prémio! Envie o seu PIN M-Pesa em http://x.co" }
```
`phone`: obrigatório (máx. 30 car.) · `message`: obrigatório, não vazio (máx. 2000 car.).

Resposta `200`:
```json
{
  "verdict": "fraud",
  "category": "phishing",
  "confidence": 1.0,
  "explanation": "Sinais encontrados: pede credenciais ou códigos; contém ligação suspeita; promete prémio; invoca operador ou banco.",
  "reputation": {
    "number": "+258841234567",
    "status": "blacklisted",
    "category": "phishing",
    "risk_score": 70,
    "report_count": 0
  }
}
```
- `category` é `null` quando `verdict = safe`.
- `confidence` vai de 0 a 1.
- `reputation` é o estado **actual** do número depois desta análise — é a base para o alerta ao utilizador. Cada classificação alimenta a reputação (uma fraude com confiança ≥ 0.8 coloca o número na blacklist).
- A mensagem é analisada e guardada; mostrar `explanation` ao utilizador.

### 2.2 Denunciar número / tentativa de burla
`POST /api/v1/public/reports/` · throttle 10/min

Pedido:
```json
{
  "phone": "+258 84 111 2222",
  "behavior": "Ligou a fingir ser do banco e pediu o PIN",
  "category": "phishing",
  "channel": "call",
  "amount_lost": "1500.00",
  "reporter_contact": "opcional@email.com"
}
```
| Campo | Obrigatório | Notas |
|---|---|---|
| `phone` | sim | |
| `behavior` | sim | texto, máx. 2000 car. |
| `category` | não | default `other` |
| `channel` | não | default `other` |
| `amount_lost` | não | decimal (até 12 dígitos, 2 casas) |
| `reporter_contact` | não | máx. 100 car.; **nunca é devolvido** pela API pública |

Resposta `201` (propositadamente reduzida):
```json
{ "id": "uuid", "number": "+258841112222", "category": "phishing", "status": "pending", "created_at": "2026-10-03T10:00:00Z" }
```
A denúncia entra como `pending` (aguarda moderação) mas já conta para a reputação: 3 denúncias activas colocam o número na blacklist.

### 2.3 Consultar reputação de um número
`GET /api/v1/public/numbers/{phone}/` · throttle 60/min

Use `encodeURIComponent` — o `+` deve ir como `%2B` (ex.: `/public/numbers/%2B258841234567/`); números sem `+` também funcionam.

Resposta `200`:
```json
{ "number": "+258841234567", "status": "suspicious", "category": "phishing", "risk_score": 20, "report_count": 1 }
```
Número nunca visto **não é 404**: devolve `status: "unknown"`, `risk_score: 0`, `category: null`, `report_count: 0`. Esta consulta não regista nada. Número inválido → 400.

---

### 2.4 Conteúdo educativo
`GET /api/v1/public/posts/` · `GET /api/v1/public/posts/{slug}/` · throttle 60/min

Só devolve publicações `published` (rascunhos nunca aparecem; `404` com `code: "post_not_found"`).

Listagem paginada (`?page`, `?size`), filtros `topic` (`scams`, `social_engineering`, `credentials`, `sim_swap`) e `?search=` (título e resumo). Mais recentes primeiro. Item (sem corpo):
```json
{ "id": "uuid", "title": "Troca de SIM explicada", "slug": "troca-de-sim-explicada", "summary": "…", "topic": "sim_swap", "cover_image_url": "", "published_at": "2026-10-03T10:00:00Z" }
```
Detalhe por `slug`: os mesmos campos + `body` (texto completo; texto simples com quebras de linha).

---

## 3. Autenticação (zona privada)

| Rota | Corpo | Resposta |
|---|---|---|
| `POST auth/login/` | `{ "email", "password" }` | `{ "access", "refresh" }` |
| `POST auth/refresh/` | `{ "refresh" }` | `{ "access" }` |
| `GET auth/me/` | — | utilizador + `claims` |

- O `access` tem vida curta (por omissão 30 min); renovar com `refresh` ao receber 401 e repetir o pedido. Refresh expirado → voltar ao login.
- O JWT traz as claims `profiles` (ex. `["esquadra"]`) e `permissions` (ex. `["occurrence:create"]`). **Use-as para mostrar/esconder menus e botões**, mas a API é quem decide (403).
- Alterações de permissões só chegam ao token no próximo refresh/login.
- `auth/me/` devolve `id, email, name, profiles, is_active, last_login, created_at, updated_at, claims`.

### Perfis e permissões da fase actual
| Perfil | Permissões |
|---|---|
| `admin` | todas |
| `esquadra` | `occurrence:create`, `occurrence:read`, `occurrence:update` |
| `entidade` | `occurrence:read` |

Moderação de blacklist/denúncias usa `blacklist:read|update` e `report:read|update` (por omissão só o `admin`).

---

## 4. Endpoints privados (moderação)

Todos exigem `Authorization: Bearer <access>` e a permissão indicada.

### 4.1 Blacklist / números
| Rota | Permissão | Descrição |
|---|---|---|
| `GET blacklist/` | `blacklist:read` | listagem paginada |
| `GET blacklist/{id}/` | `blacklist:read` | detalhe |
| `PATCH blacklist/{id}/` | `blacklist:update` | moderar |

Filtros: `status`, `category` · pesquisa: `?search=` (no número).

Item:
```json
{
  "id": "uuid", "number": "+258841234567", "status": "blacklisted", "category": "phishing",
  "risk_score": 80, "report_count": 3, "classification_count": 5, "fraud_count": 2,
  "first_seen_at": "…", "last_reported_at": "…", "blacklisted_at": "…", "updated_at": "…"
}
```
`PATCH` aceita `{ "status"?, "category"? }`. Marcar `status: "cleared"` **limpa** o número: `risk_score` → 0, `report_count` → 0, `blacklisted_at` → `null` e as denúncias activas desse número passam a `rejected`. Marcar `blacklisted` define `blacklisted_at`. Devolve o item actualizado.

### 4.2 Denúncias
| Rota | Permissão | Descrição |
|---|---|---|
| `GET reports/` | `report:read` | listagem paginada |
| `GET reports/{id}/` | `report:read` | detalhe |
| `PATCH reports/{id}/` | `report:update` | moderar |

Filtros: `status`, `category`, `channel`, `phone_number__number` (E.164 exacto) · pesquisa: `?search=` (número e texto do comportamento).

Item (aqui o `reporter_contact` e o `reporter_ip` **são** visíveis — dados sensíveis, mostrar só a moderadores):
```json
{
  "id": "uuid", "number": "+258841112222", "category": "phishing", "behavior": "…", "channel": "call",
  "amount_lost": "1500.00", "reporter_contact": "…", "reporter_ip": "1.2.3.4",
  "status": "pending", "moderation_note": "", "created_at": "…", "updated_at": "…"
}
```
`PATCH` aceita `{ "status"?, "moderation_note"? }`. Rejeitar uma denúncia (`rejected`) retira-a da contagem do número.

---

## 5. Limites de pedidos (throttling)
Por IP e por minuto: classificar **20**, denunciar **10**, consultar reputação **60**. Ao exceder: `429` com `code: "throttled"` e header `Retry-After`. Recomendações: desactivar o botão durante o pedido; no 429, mostrar mensagem amigável e esperar `Retry-After`; fazer *debounce* na consulta de reputação (não consultar a cada tecla).

## 6. Fluxos sugeridos

**Ecrã “Verificar mensagem”**: dois campos (número, mensagem) → `POST public/classify/` → mostrar veredicto, `explanation` e um cartão de reputação com `reputation.status`/`risk_score`. Oferecer o botão “Denunciar este número” que abre o formulário de denúncia já com o número preenchido.

**Ecrã “Denunciar”**: formulário de 2.2 → após `201` mostrar confirmação (não há dados sensíveis na resposta).

**Pesquisa rápida de número**: `GET public/numbers/{phone}/` com debounce → badge com o estado.

**Backoffice (moderador)**: login → listas de `blacklist/` e `reports/` com filtros por `status`; acções de `PATCH` conforme as permissões do `claims.permissions`.

## 7. Notas
- IDs são UUID. Datas em ISO 8601 (UTC).
- Os números dos endpoints públicos não precisam de ser validados no cliente além de “não vazio”; a API devolve 400 com mensagem em português.
- A classificação actual usa regras locais; o provider de IA será trocado no servidor sem alterar este contrato.

---

## 8. Gestão de conteúdo educativo (privado)

Todos exigem `Authorization: Bearer <access>`.

| Rota | Permissão | Descrição |
|---|---|---|
| `GET posts/` | `education:read` | listagem paginada **com rascunhos** |
| `POST posts/` | `education:create` | criar (entra como `draft`) |
| `GET posts/{id}/` | `education:read` | detalhe |
| `PATCH posts/{id}/` | `education:update` | editar / publicar |
| `DELETE posts/{id}/` | `education:delete` | remover (204) |

Filtros: `status` (`draft`, `published`), `topic` · pesquisa: `?search=`.

Escrita (`POST`/`PATCH`): `{ "title", "summary"?, "body", "topic", "status"?, "cover_image_url"? }`. `title`, `body` e `topic` são obrigatórios na criação; o `slug` é gerado a partir do título e **não muda** depois. Passar `status: "published"` define `published_at` na primeira publicação. Resposta: `id, title, slug, summary, body, topic, status, cover_image_url, published_at, is_active, created_at, updated_at`.

## 9. Ocorrências de documentos perdidos (privado)

Criadas por utilizadores do perfil `esquadra` e consultadas por `entidade` (ou `esquadra`). Todos exigem `Authorization: Bearer <access>`.

| Rota | Permissão | Descrição |
|---|---|---|
| `GET occurrences/` | `occurrence:read` | listagem paginada |
| `POST occurrences/` | `occurrence:create` | criar ocorrência |
| `GET occurrences/{id}/` | `occurrence:read` | detalhe |
| `PATCH occurrences/{id}/` | `occurrence:update` | actualizar / fechar |

Não há `DELETE` (as ocorrências ficam como registo). Filtros exactos: `status` (`open`, `found`, `closed`), `document_type` (`bi`, `passport`, `driving_license`, `dire`, `other`), `document_number`, `station_name`, `reference` · pesquisa: `?search=` (referência, nº do documento, nome do titular). Para uma entidade encontrar um documento, use `?document_number=…` (exacto, em maiúsculas).

Criar (`POST`):
```json
{
  "document_type": "bi",
  "document_number": "1100123456A",
  "owner_name": "Ana Macuácua",
  "owner_contact": "84 111 2222",
  "lost_at": "2026-09-30",
  "location": "Mercado Central",
  "description": "Perdido num táxi",
  "station_name": "Esquadra da Polícia Nº 1"
}
```
Obrigatórios: `document_type`, `document_number`, `owner_name`, `lost_at`, `location`, `station_name`. `document_number` é guardado em maiúsculas e sem espaços nas pontas. `lost_at` (AAAA-MM-DD) não pode ser futura. Uma ocorrência nova começa sempre `open` (enviar outro `status` → 400).

Resposta (`201` e leituras):
```json
{
  "id": "uuid", "reference": "OC-2026-000001", "document_type": "bi", "document_number": "1100123456A",
  "owner_name": "Ana Macuácua", "owner_contact": "84 111 2222", "lost_at": "2026-09-30",
  "location": "Mercado Central", "description": "Perdido num táxi", "status": "open",
  "station_name": "Esquadra da Polícia Nº 1", "registered_by": "Agente Silva",
  "closed_at": null, "created_at": "…", "updated_at": "…"
}
```
`reference` é gerada pela API, sequencial por ano, e **imutável**. `PATCH` aceita os mesmos campos; `status: "closed"` preenche `closed_at` e voltar a `open`/`found` limpa-o. São dados pessoais: mostrar só a utilizadores autenticados com permissão e não os registar em logs do cliente.
