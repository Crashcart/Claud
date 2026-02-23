# ─── Brainerd AI — Docker image ───────────────────────────────────────────────
# Low-CPU optimized: single uvicorn worker, async I/O throughout.
# Lots of disk available — model data stored in named volumes.

FROM python:3.12-slim

LABEL maintainer="brainerd"
LABEL description="Brainerd AI — Ollama + optional Google AI hub for chat and RPG"

# System deps (curl for healthcheck, no build tools needed — pure Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Data directory for SQLite (mounted as volume in compose)
RUN mkdir -p /data

# Non-root user for security
RUN useradd -m -u 1000 brainerd && chown -R brainerd:brainerd /app /data
USER brainerd

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/health/ || exit 1

# Single worker — this is an async app, one worker is sufficient for low-CPU
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
