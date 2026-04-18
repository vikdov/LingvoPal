# Use a multi-stage or grab uv from the official image
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install system dependencies (curl added for healthcheck)
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install dependencies using the lockfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check using curl (more reliable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Use the virtualenv created by uv
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
