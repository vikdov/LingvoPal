FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# System deps — gcc/libpq for asyncpg/psycopg build; curl for healthcheck
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cached until lockfile changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy application code (after deps so code changes don't bust dep cache)
COPY . .

# Activate the venv for all subsequent RUN/CMD instructions
ENV PATH="/app/.venv/bin:$PATH"

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production: no --reload, single worker (scale via replicas)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
