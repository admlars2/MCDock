############################################################
# Stage 1 – build React assets
############################################################
FROM node:20-alpine AS ui-build

ENV VITE_API_BASE=/api

WORKDIR /ui
COPY frontend/ ./
RUN npm ci --legacy-peer-deps && npm run build
 
# Collect the compiled output in one predictable place
RUN mkdir /ui/out && cp -r dist/* /ui/out/


############################################################
# Stage 2 – build Python wheels & freeze deps
############################################################
FROM python:3.11-slim AS py-build

ARG POETRY_VERSION=1.8.2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=${POETRY_VERSION}

# -- build-time system deps only
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY backend/pyproject.toml backend/poetry.lock* ./

# Produce a reproducible requirements.txt and pre-build wheels
RUN poetry export --only main --without-hashes --format requirements.txt > requirements.txt \
 && pip wheel --no-deps -r requirements.txt -w /tmp/wheels


############################################################
# Stage 3 – runtime image (API + static files)
############################################################
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=prod

# --- system deps -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg lsb-release

# --- add Docker’s official repo ---------------------------------
RUN install -m 0755 -d /etc/apt/keyrings \
 && curl -fsSL https://download.docker.com/linux/debian/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
 && echo \
   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian \
        $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
   > /etc/apt/sources.list.d/docker.list

# --- install CLI + compose plugin -------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        docker-ce-cli docker-compose-plugin \
 && rm -rf /var/lib/apt/lists/*

# ───────── create non-root user ─────────────────────────
WORKDIR /app

# ───────── install wheels built in previous stage ───────
COPY --from=py-build /tmp/wheels /tmp/wheels
RUN pip install --no-index --find-links=/tmp/wheels /tmp/wheels/*

# ───────── project source + static files ────────────────
COPY backend/ ./
RUN mkdir -p mcdock/static
COPY --from=ui-build /ui/out/ mcdock/static/

EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "mcdock.main:app"]