# ---- build: instala dependências com uv e recolhe estáticos ----
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_CACHE=1
WORKDIR /app

# INSTALL_DEV=true inclui o grupo dev (ipython, pytest...) — o compose liga-o, produção não
ARG INSTALL_DEV=false
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project $([ "$INSTALL_DEV" = "true" ] || echo --no-dev)

COPY . .
RUN SECRET_KEY=build-only .venv/bin/python manage.py collectstatic --noinput

# ---- runtime: apenas o necessário para correr ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH" HOME=/tmp
WORKDIR /app

COPY --from=build /app /app
RUN useradd --system --no-create-home --no-log-init app
USER app

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
