# Mozcyber Solution API

API em Django REST Framework, organizada em camadas, com login por email, JWT com perfis e permissões nas claims, auditoria de ações, paginação, versionamento e Swagger.

> Regras de arquitetura, convenções e o passo a passo para criar novas funcionalidades estão em [CLAUDE.md](CLAUDE.md). Leia-o antes de contribuir.

## Funcionalidades

- **Autenticação por email** com `User` customizado e JWT (`djangorestframework-simplejwt`).
- **Permissões granulares por método HTTP** com o decorador `@require_permissions("user:read")`. Perfis e permissões vão nas claims `profiles` e `permissions` do token, por isso a validação não consulta a base de dados.
- **Camadas obrigatórias em cada app**: `views → services → repositories → models`, mais `serializers`, `urls`, `utils` e `tests`.
- **Sem N+1**: os repositories declaram `select_related` e `prefetch_related`, e os testes verificam o número de queries.
- **Auditoria genérica** (`audit_log`): guarda ação, utilizador, IP, user-agent, método, payload (sem segredos) e mais, para qualquer app.
- **API paginada** (`?page=&size=`), **versionada** (`/api/v1/`) e documentada com **Swagger**.
- **Erros uniformes**: `{"code", "message", "details"}`.
- **Docker**: Postgres, gunicorn e WhiteNoise.

## Stack

Python 3.12 · Django 5.1 · DRF · simplejwt · drf-spectacular · PostgreSQL · gunicorn · WhiteNoise · django-cors-headers · `uv` · pytest · ruff · ipython (dev)

## Começar

### Com Docker (recomendado)

```bash
cp .env.example .env            # ajuste WEB_PORT se a 8000 estiver ocupada
docker compose up --build
```

Ao arrancar, o container corre `migrate` e `seed_access`, que cria as permissões e o perfil `admin`.

Crie um utilizador administrador:

```bash
docker compose exec web python manage.py createsuperuser   # login por email
docker compose exec web python manage.py shell             # IPython
```

Para dar acesso total à API a um utilizador, associe-lhe o perfil `admin`:

```bash
docker compose exec web python manage.py shell -c "
from apps.user.models import User, Profile
u = User.objects.get(email='voce@exemplo.com')
u.profiles.add(Profile.objects.get(code='admin'))"
```

### Local (sem Docker)

Precisa do [uv](https://docs.astral.sh/uv/). Sem `DATABASE_URL`, usa SQLite.

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py seed_access
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Endereços

| O quê | URL |
|---|---|
| Swagger UI | `/api/docs/` |
| Schema OpenAPI | `/api/schema/` |
| API v1 | `/api/v1/` |
| Admin Django | `/admin/` |

## Usar a API

```bash
# 1. login (devolve access e refresh)
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email": "voce@exemplo.com", "password": "sua-password"}'

# 2. chamar um endpoint protegido (paginado)
curl 'http://localhost:8000/api/v1/users/?page=1&size=10&search=ana' \
  -H 'Authorization: Bearer <access>'
```

Claims do token:

```json
{ "profiles": ["admin"], "permissions": ["user:read", "user:create", "log:read"] }
```

### Endpoints

| Recurso | Rotas | Permissões |
|---|---|---|
| Auth | `POST /auth/login/`, `POST /auth/refresh/`, `GET /auth/me/` | públicas, exceto `me` (autenticado) |
| Utilizadores | `/users/`, `/users/{id}/` | `user:read\|create\|update\|delete` |
| Perfis | `/profiles/`, `/profiles/{id}/` | `profile:read\|create\|update\|delete` |
| Permissões | `/permissions/`, `/permissions/{id}/` | `permission:read\|create\|update\|delete` |
| Logs | `GET /logs/` | `log:read` |

Todas as rotas acima ficam sob `/api/v1/`. As listagens aceitam `page`, `size` e `search`, além de filtros próprios (ver Swagger).

Respostas de erro:

```json
{ "code": "permission_denied", "message": "Sem permissão para esta acção.", "details": null }
```

## Estrutura

```
config/          settings, urls, api_urls (rotas versionadas)
apps/
  core/          BaseModel, exceções, paginação, permissões, repository/service/view base
  user/          User, Profile, Permission, autenticação JWT
  audit_log/     ActionLog, LogService, LoggingMixin
Dockerfile · docker-compose.yml · .env.example · CLAUDE.md
```

## Desenvolvimento

```bash
uv run pytest                              # testes (--cov=apps para cobertura)
uv run ruff check --fix . && uv run ruff format .
uv run python manage.py spectacular --validate --fail-on-warn   # valida o OpenAPI
uv add <pacote>                            # nova dependência (--dev para desenvolvimento)
```

Cada funcionalidade ou endpoint novo precisa de testes: sucesso, 401, 403, validação e, nas listagens, paginação e ausência de N+1. Os detalhes e o checklist completo estão no [CLAUDE.md](CLAUDE.md).

## Configuração

| Variável | Descrição | Padrão |
|---|---|---|
| `SECRET_KEY` | chave secreta do Django (**mude em produção**) | chave de desenvolvimento |
| `DEBUG` | modo debug | `False` |
| `ALLOWED_HOSTS` | hosts permitidos, separados por vírgula | `*` |
| `DATABASE_URL` | ex.: `postgres://user:pass@host:5432/db` | SQLite local |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | credenciais do Postgres no compose | `mozcyber` |
| `ACCESS_TOKEN_MINUTES` / `REFRESH_TOKEN_DAYS` | validade dos tokens | `30` / `7` |
| `WEB_PORT` | porta publicada no host | `8000` |
| `INSTALL_DEV` | instala dependências de desenvolvimento na imagem (ipython, pytest) | `true` no compose, `false` no Dockerfile |

## Produção

- Defina `SECRET_KEY` forte, `DEBUG=False` e `ALLOWED_HOSTS`.
- Construa a imagem sem dependências de desenvolvimento: `docker build --build-arg INSTALL_DEV=false .` (cerca de 313 MB, contra 464 MB com as dependências de desenvolvimento).
- Os ficheiros estáticos são servidos pelo WhiteNoise, e o gunicorn corre com 3 workers como utilizador não-root.
- O CORS está aberto a todas as origens (`CORS_ALLOW_ALL_ORIGINS`). A autenticação usa o header `Authorization`, sem cookies. Para restringir, use `CORS_ALLOWED_ORIGINS` em [config/settings.py](config/settings.py).
- Alterações de permissões só chegam ao token no próximo refresh ou login.
