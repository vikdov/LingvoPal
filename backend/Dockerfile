FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# System deps — gcc/libpq for asyncpg/psycopg build; curl for healthcheck.
# apt-get upgrade patches base-image CVEs (libcap2 CVE-2026-4878,
# linux-libc-dev CVE-2026-43494) that Trivy flags as fixable HIGH.
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
  gcc \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Upgrade the base image's system pip to clear fixable CVEs Trivy flags
# (CVE-2026-3219, CVE-2026-6357 — fixed in pip 26.1).
RUN pip install --no-cache-dir --upgrade 'pip>=26.1'

# Install Python deps first (layer cached until lockfile changes).
# uv is only needed to build the venv; remove it afterwards so Trivy does
# not flag the rustls-webpki HIGH (GHSA-82j2-j2ch-gfr8) bundled in the binary.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache && rm -f /bin/uv

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
