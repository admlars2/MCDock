# ─────────────── Stage 1: build React ────────────────
FROM node:20-alpine AS ui-build

WORKDIR /ui
COPY frontend/ ./
RUN npm ci --legacy-peer-deps \
 && npm run build        # vite → dist /  CRA → build

RUN mkdir /ui/out \
 && cp -r $( [ -d dist ] && echo dist || echo build )/* /ui/out/

# ─────────────── Stage 2: API + static ───────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1

# 1) system deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

# 2) Poetry + deps
ENV POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN poetry install --only main --no-interaction --no-ansi

# 3) project source
COPY backend/ ./

# 4) compiled UI → FastAPI static dir  (note path!)
RUN mkdir -p src/mcdock/static
COPY --from=ui-build /ui/out/ src/mcdock/static/

# 5) runtime
EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "python:gunicorn_conf", "src.mcdock.main:app"]