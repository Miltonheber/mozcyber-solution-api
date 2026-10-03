# Mozcyber Solution API — guia do projecto

Documento orientador para qualquer dev ou IA que continue este projecto. **Leia antes de escrever código e mantenha-o actualizado.**

## 1. Stack
Python 3.12 · Django 5.1 · Django REST Framework (**`APIView`**, sem ViewSets/generics) · `djangorestframework-simplejwt` · `drf-spectacular` (Swagger) · MySQL 8.4 via `mysqlclient` (SQLite como fallback local) · `gunicorn` · `whitenoise` · `django-environ` · gestão de dependências com **`uv`** · shell com `ipython` (dev), testes com `pytest` + `pytest-django` + `factory-boy` · lint/format com `ruff`.

## 2. Comandos
```bash
uv sync                                   # instalar dependências
uv add <pkg> / uv add --dev <pkg>         # adicionar dependência
uv run python manage.py migrate
uv run python manage.py seed_access       # cria permissões do catálogo + perfil admin (idempotente)
uv run python manage.py createsuperuser   # login por email
uv run python manage.py runserver 8082   # porta do backend (o frontend usa 8081)
uv run python manage.py shell            # shell interactivo com IPython (dev dep) e models auto-importados
uv run pytest [-k nome] [--cov=apps]      # testes (usa SQLite por omissão, --reuse-db)
uv run ruff check --fix . && uv run ruff format .
uv run python manage.py spectacular --validate --fail-on-warn   # valida o OpenAPI

docker compose exec web python manage.py shell   # IPython dentro do container
docker compose up --build                 # db (mysql) + web (gunicorn); porta via WEB_PORT (default 8082)
```
Config por `.env` (copiar de `.env.example`). Sem `DATABASE_URL` usa `db.sqlite3`; o compose injecta o URL do MySQL. **SQLite local e MySQL do Docker são bases diferentes**; para partilhar, subir `db` e pôr `DATABASE_URL=mysql://mozcyber:mozcyber@127.0.0.1:3307/mozcyber` no `.env`.
Swagger: `/api/docs/` · schema: `/api/schema/`. O container corre `migrate` + `seed_access` no arranque ([docker-entrypoint.sh](docker-entrypoint.sh)).

## 3. Estrutura
```
config/            settings.py, urls.py, api_urls.py (rotas versionadas), wsgi/asgi
apps/
  core/            BaseModel, exceptions, exception_handler, pagination, permissions (HasPermission),
                   BaseRepository, BaseService, BaseAPIView + mixins CRUD, schema (OpenAPI), utils, testing/
  user/            User (login por email), Profile, Permission, auth JWT, CRUD
  audit_log/       ActionLog genérico + LogService + LoggingMixin
  reputation/      PhoneNumber (blacklist/reputação), MessageClassification (histórico da IA), NumberReport (denúncias/burlas)
  education/       Post (conteúdo educativo; público só `published`)
  occurrences/     LostDocumentOccurrence (documentos perdidos; criada por perfil `esquadra`, lida por `entidade`)
```
**Domínio:** zona **pública** (classificar, denunciar, ler posts) vs **privada** (publicar posts, ocorrências, moderação). Registos criados por anónimos têm `created_by = null`. Números sempre normalizados com `normalize_phone` ([apps/core/utils.py](apps/core/utils.py)) antes de gravar/consultar. Esquadras/entidades são apenas Profiles (`esquadra`, `entidade`, criados por `seed_access`; `station_name` na ocorrência identifica a esquadra). Fase 1 (reputation) implementada; `education` e `occurrences` só têm modelos.
**Cada app tem obrigatoriamente** as camadas: `models`, `repositories/`, `services/`, `serializers/`, `views/`, `urls` (módulo ou pacote), `utils/`, `tests/`.

## 4. Arquitectura em camadas (regra de ouro)
`URL → View → Service → Repository → Model`. Dependências só descem.

| Camada | Responsabilidade | NÃO pode |
|---|---|---|
| **View** (`BaseAPIView`) | Auth/permissões (`@require_permissions`), validar entrada com serializer, chamar o service, serializar saída, paginar | Conter regras de negócio ou queries/ORM |
| **Service** (`BaseService`) | Regras de negócio, orquestração, levantar exceptions de negócio, hash de password etc. | Conhecer `request`/HTTP/serializers; usar ORM directamente |
| **Repository** (`BaseRepository`) | **Único** ponto de acesso ao ORM; `select_related`/`prefetch_related` declarados na classe | Regras de negócio |
| **Serializer** | Validação de formato e representação | Persistir dados |
| **utils** | Funções puras/auxiliares reutilizáveis | Estado global |

- Services recebem o repository por injecção (`Service(repository=...)`) → fáceis de testar com mocks.
- SOLID/KISS/DRY: o que se repete vai para `core` (ex.: CRUD completo = compor os mixins de [apps/core/views.py](apps/core/views.py) + declarar atributos). Não criar abstracções antes de haver repetição real.
- Views são **`APIView`**: um método por verbo HTTP. O CRUD vem dos mixins em [apps/core/views.py](apps/core/views.py) (`ListMixin.list`, `CreateMixin.create`, `RetrieveMixin.retrieve`, `UpdateMixin.partial_update`, `DestroyMixin.destroy`). Os mixins só fornecem a lógica; a view declara cada método HTTP explicitamente (`get`, `post`…), com o seu `@require_permissions`, e delega no mixin.

## 5. Anti N+1 (obrigatório)
- Todo o acesso a dados passa por repository; declarar `select_related` (FK/OneToOne) e `prefetch_related` (M2M/reverso) na classe — aplicam-se a `list` e `get`.
- Serializers que mostram relações devem usar só o que está pré-carregado (nested/Slug de M2M prefetched). Nunca aceder a relações não declaradas no repository.
- Cada listagem tem teste com `django_assert_max_num_queries(...)` com vários registos relacionados (ver `test_list_has_constant_queries_no_n_plus_1`).
- `service.create/update` recarregam a instância via `repository.get` para devolver com os prefetches.

## 6. API: prefixo, versão, paginação, erros
- Tudo em `/api/<versão>/...` (`URLPathVersioning`, versões permitidas em `ALLOWED_VERSIONS`, hoje `v1`). Novas rotas entram em [config/api_urls.py](config/api_urls.py). `reverse()` precisa de `kwargs={"version": "v1"}`.
- Paginação: `?page=1&size=20` (size máx. 100) → `{count, next, previous, results}` ([apps/core/pagination.py](apps/core/pagination.py)). Listagens usam `self.paginate(qs, request)`.
- Filtros/pesquisa: o repository declara `filter_fields` (filtros exactos permitidos via query param) e `search_fields` (`?search=`). Params fora da whitelist são ignorados.
- **Erros** têm sempre o formato `{"code": str, "message": str, "details": any|null}`. Para erros de negócio, o service levanta uma `BusinessException` de [apps/core/exceptions.py](apps/core/exceptions.py) (`ValidationException` 400, `UnauthorizedException` 401, `PermissionDeniedException` 403, `NotFoundException` 404, `ConflictException` 409). Nunca devolver `Response` de erro à mão. Códigos próprios: `raise NotFoundException("...", code="user_not_found")`.
- Swagger: `BaseAutoSchema` ([apps/core/schema.py](apps/core/schema.py)) gera o OpenAPI a partir de `read_serializer_class`/`write_serializer_class`/`service_class`. Views fora do padrão (login…) usam `@extend_schema`. Validar com `spectacular --validate --fail-on-warn`.

## 7. Autenticação e permissões
- `User` ([apps/user/models/user.py](apps/user/models/user.py)): `USERNAME_FIELD = "email"`, herda `BaseModel`; `AUTH_USER_MODEL = "user.User"`.
- Modelo de acesso: `User —M2M→ Profile —M2M→ Permission`. Códigos de permissão: `recurso:acção` (ex. `user:read`).
- **Catálogo** de permissões em [apps/user/constants.py](apps/user/constants.py) (`PERMISSION_CATALOG`). Endpoint novo ⇒ acrescentar o código aqui; `seed_access` cria-o e atribui ao perfil `admin`.
- Consulta central: `get_user_permissions(user)` e `get_user_profiles(user)` em [apps/user/utils/permissions.py](apps/user/utils/permissions.py) (1 query cada, só perfis/permissões activos).
- **JWT**: login em `POST /api/v1/auth/login/` devolve `{access, refresh}`. Claims próprias no token (construídas em [apps/user/utils/tokens.py](apps/user/utils/tokens.py) → `build_tokens`):
  - `profiles`: `["admin", ...]`
  - `permissions`: `["user:read", "user:create", ...]`
  - `POST /api/v1/auth/refresh/` recalcula as claims a partir da BD. Alterações de permissões só chegam ao token no próximo refresh/login (access curto: `ACCESS_TOKEN_MINUTES`).
- Autorização nas views, **granular por método HTTP**, com o decorador `@require_permissions` ([apps/core/permissions.py](apps/core/permissions.py)):
  ```python
  @require_permissions("user:read")
  def get(self, request, *args, **kwargs):
      return self.list(request)
  ```
  `HasPermission` lê o decorador do handler do método e valida contra a claim `permissions` do token **sem tocar na BD**; exige TODAS as permissões listadas. Método sem decorador ⇒ basta estar autenticado (default global `IsAuthenticated`). Não existe `required_permissions` ao nível da classe.
- `GET /api/v1/auth/me/` devolve o utilizador e as claims.

### Views públicas (sem autenticação)
- Herdam `PublicAPIView` ([apps/core/views.py](apps/core/views.py)): sem JWT, `AllowAny`, `ScopedRateThrottle`. **Obrigatório** `throttle_scope` (taxas em `DEFAULT_THROTTLE_RATES`: `public_classify`, `public_report`, `public_read`). A cache de throttling é por processo (LocMem) — com vários workers o limite efectivo multiplica; para limite global usar Redis/DB cache.
- Views públicas usam `@extend_schema` e serializers **reduzidos** (nunca expor IP/contacto do denunciante). Os mixins CRUD usam `self.get_actor(request)` (`None` para anónimos).
- Rotas públicas em `/api/v1/public/…` (`classify/`, `reports/`, `numbers/<phone>/`); moderação autenticada em `blacklist/` e `reports/`.
- Classificação: `settings.MESSAGE_CLASSIFIER` (env) aponta para a classe que implementa `MessageClassifier` ([apps/reputation/services/classifier.py](apps/reputation/services/classifier.py)); default `RuleBasedClassifier`. Reputação (score/blacklist) em [apps/reputation/utils/scoring.py](apps/reputation/utils/scoring.py); contadores sempre recontados dos registos.

## 8. BaseModel
[apps/core/models.py](apps/core/models.py): `id` (UUID), `created_at`, `updated_at`, `created_by`, `updated_by` (FK ao user, `related_name="+"`), `is_active`; ordering por `-created_at`. Todos os modelos de negócio herdam dele. `created_by/updated_by` são preenchidos pelo `BaseRepository.create/update(actor=request.user)` — os mixins de view já passam o actor. Em modelos com `Meta` próprio: `class Meta(BaseModel.Meta)`.

## 9. Auditoria (app `audit_log`)
- Modelo genérico `ActionLog`: user, action (`user.create`), resource_type/resource_id (strings, sem GenericFK), method, path, status_code, payload (redigido), ip, user_agent, extra, created_at.
- Automático nas views: `class MinhaView(LoggingMixin, CreateMixin, BaseAPIView): log_actions = {"POST": "x.create"}; log_resource_type = "x"` (o `LoggingMixin` vai **primeiro** nos bases). Regista respostas < 500; falha ao gravar nunca quebra o pedido.
- Manual (jobs, services): `LogService().record("acção", user=..., request=..., resource_type=..., resource_id=..., payload=..., extra=...)`.
- Segredos (`password`, `token`, `access`, `refresh`…) são mascarados por `redact` ([apps/core/utils.py](apps/core/utils.py)); acrescentar chaves em `SENSITIVE_KEYS` se necessário.
- Consulta: `GET /api/v1/logs/` (permissão `log:read`; filtros `user_id, action, resource_type, resource_id, method, status_code, search`).

## 10. Testes (cada funcionalidade/endpoint nasce com testes)
- Cada app: `tests/test_services.py`, `test_repositories.py`, `test_views*.py`, `test_utils.py` + `factories.py` (factory-boy).
- Fixtures globais ([apps/core/testing/fixtures.py](apps/core/testing/fixtures.py), carregadas pelo [conftest.py](conftest.py)): `api_client`, `user`, e **`auth_client(["perm:a", ...])`** → `APIClient` com JWT real e essas permissões (`client.user` é o utilizador). Hash de password rápido é automático.
- Helpers ([apps/core/testing/helpers.py](apps/core/testing/helpers.py)): `grant_permissions`, `bearer`, `assert_error(response, status, code)`, `assert_paginated(response, count, size)`.
- **Mínimo por endpoint**: sucesso · 401 (sem token) · 403 (sem permissão) · validação (400) · 404 quando há `pk` · paginação/filtros em listagens · teste de queries (anti N+1) em listagens.
- Services: testar sem BD com `MagicMock` no repository sempre que possível (ver `test_user_service_hashes_password_without_db`); regras que dependem do ORM usam `@pytest.mark.django_db`.
- Antes de concluir qualquer tarefa: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`.

## 11. Checklist: nova funcionalidade / nova app
1. (App nova) criar `apps/<nome>/` com `apps.py` (`name="apps.<nome>"`, `label`), pacotes `repositories/ services/ serializers/ views/ utils/ tests/`, `urls`; registar em `INSTALLED_APPS`; incluir rotas em [config/api_urls.py](config/api_urls.py).
2. Modelo herdando `BaseModel`; `uv run python manage.py makemigrations <app>`.
3. Repository herdando `BaseRepository` (`model`, `select_related`, `prefetch_related`, `filter_fields`, `search_fields`).
4. Service herdando `BaseService` (`repository_class`); regras de negócio aqui, erros via exceptions do `core`.
5. Serializers `*ReadSerializer` / `*WriteSerializer` (read só usa relações pré-carregadas).
6. Views: `LoggingMixin` + mixins CRUD + `BaseAPIView` (ou só `BaseAPIView` + `@extend_schema` para casos custom) com `service_class`, serializers, `log_actions`; métodos `get/post/patch/delete` com `@require_permissions(...)` (ver [apps/user/views/users.py](apps/user/views/users.py) como modelo).
7. Acrescentar permissões novas a `PERMISSION_CATALOG`.
8. Escrever os testes (secção 10) e correr lint + testes + `spectacular --validate`.
9. Actualizar este ficheiro se mudar alguma regra.

## 12. Docker
- [Dockerfile](Dockerfile): multi-stage, `python:3.12-slim`; stage `build` instala `gcc`/headers MySQL (para compilar `mysqlclient`) e deps com `uv sync --frozen --no-dev` e corre `collectstatic`; stage final só leva `/app` (+ venv) e `libmariadb3`, corre como utilizador não-root com **gunicorn** (`config.wsgi`, 3 workers).
- [docker-compose.yml](docker-compose.yml): `db` (mysql:8.4, utf8mb4, healthcheck, volume `mysqldata`, porta do host `DB_PORT`=3307) e `web` (espera o db saudável; `DATABASE_URL` montado a partir de `DB_*`). Porta do host: `WEB_PORT`. `down -v` apaga os dados.
- Estáticos: **WhiteNoise** logo a seguir ao `SecurityMiddleware`, `CompressedManifestStaticFilesStorage`, `STATIC_ROOT=staticfiles/`. Em produção definir `SECRET_KEY` forte, `DEBUG=False`, `ALLOWED_HOSTS`.
- `INSTALL_DEV` (build arg, default `false` no Dockerfile, `true` no compose) inclui o grupo `dev` (ipython, pytest) na imagem; em produção usar `INSTALL_DEV=false`. Dependências novas: `uv add ...` e fazer commit do `uv.lock` (o build usa `--frozen`).

## 13. CORS
`django-cors-headers` com `CORS_ALLOW_ALL_ORIGINS = True` (todas as origens), `CorsMiddleware` logo após o WhiteNoise. Seguro aqui porque a auth é por header `Authorization: Bearer` (sem cookies/credenciais). Para restringir: trocar por `CORS_ALLOWED_ORIGINS`.

## 14. Variáveis de ambiente
`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `DB_NAME/USER/PASSWORD/ROOT_PASSWORD`, `DB_PORT`, `ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_DAYS`, `MESSAGE_CLASSIFIER`, `WEB_PORT`, `INSTALL_DEV` (ver [.env.example](.env.example)).
