# Stage 1: builder — install dependencies into an isolated virtualenv with pip

FROM python:3.12-slim AS builder

WORKDIR /app

# Ensure latest pip and wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements manifest first (layer-cache friendly)
COPY requirements.txt .

# Create venv and install dependencies
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime — minimal image, non-root user

FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the compiled virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Create a non-root user (uid/gid 1001)
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home --shell /sbin/nologin appuser

# Copy application source and scripts
COPY app/ ./app/
COPY scripts/ ./scripts/

# Ensure non-root ownership
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# --log-config none: structlog formats all output as JSON to stdout/stderr
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "none"]
