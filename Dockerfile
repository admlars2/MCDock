# ------------------------ build stage ------------------------
# Use the slim variant to keep the final image light‑weight
FROM python:3.11-slim AS builder

# Install Poetry (pin the version so builds are reproducible)
ENV POETRY_VERSION=1.8.2 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1

RUN pip install "poetry==${POETRY_VERSION}"

# Copy only dependency files first (leverages layer caching)
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# If you don’t commit poetry.lock yet, the wildcard keeps the build happy
RUN poetry export --without-hashes -f requirements.txt -o requirements.txt && \
    python -m pip install --upgrade --no-cache-dir -r requirements.txt --prefix /install && \
    python -m pip install --upgrade --no-cache-dir gunicorn "uvicorn[standard]" --prefix /install

# ------------------------ runtime stage ---------------------
FROM python:3.11-slim

# Copy virtualenv from the builder image → slimmer than `pip install` again
COPY --from=builder /install /usr/local

# Copy the application source
WORKDIR /app
COPY . /app

# Environment defaults (override with -e at runtime)
ENV MC_ROOT=/data/minecraft \
    CONTROL_PANEL_BEARER_TOKEN=changeme-token \
    PYTHONPATH=/app

# Expose the default FastAPI port
EXPOSE 8000

# Create the data directory as a named volume so host paths are optional
VOLUME ["/data/minecraft"]

# Start with Uvicorn (single-process by default). For >1 CPU you can
# use `--workers` or switch the CMD to gunicorn.
CMD ["uvicorn", "src.mcdock.main:app", "--host", "0.0.0.0", "--port", "8000"]
