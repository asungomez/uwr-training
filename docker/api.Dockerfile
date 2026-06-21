# Dev image for the FastAPI app (uvicorn with live reload), managed by uv.
FROM python:3.12-slim

# uv: fast Python package/dependency manager.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/api

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Install deps first so the layer caches when only source changes.
COPY api/pyproject.toml api/uv.lock* ./
RUN uv sync --frozen --no-install-project 2>/dev/null || uv sync --no-install-project

# Source is bind-mounted at runtime; this COPY is a fallback for standalone use.
COPY api/ ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
