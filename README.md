# Mozcyber Solution API

API Django/DRF em camadas, com JWT por email (perfis e permissões em claims), auditoria de acções, paginação, versionamento e Swagger.

```bash
cp .env.example .env
docker compose up --build        # http://localhost:8000/api/docs/
# ou localmente
uv sync && uv run python manage.py migrate && uv run python manage.py seed_access && uv run python manage.py runserver
uv run pytest
```

Regras, arquitectura e fluxo de desenvolvimento: ver [CLAUDE.md](CLAUDE.md).
