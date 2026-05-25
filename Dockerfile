# ─────────────────────────────────────────────────────────────────
# RAJ DEV — Telegram File Renamer Bot
# Developer  : Raj Dev (@raj_dev_01)
# Base Image : python:3.10-slim
# Target     : Koyeb / Render / Railway / Any Docker Host
# ─────────────────────────────────────────────────────────────────

# ── Stage: Runtime ───────────────────────────────────────────────
FROM python:3.10-slim

# Metadata labels
LABEL maintainer="Raj Dev <@raj_dev_01>"
LABEL description="Telegram File Renamer Bot — Production Build"
LABEL version="1.0.0"

# ── System-level setup ───────────────────────────────────────────
# Install build tools AND Rust compiler needed for cryptg (C/Rust extension)
# Clean up apt cache in the same layer to keep image size minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
        cargo \
        rustc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────
# Copy requirements first so Docker can cache this layer separately
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────
COPY raj_dev_renamer_bot.py .

# ── Persistent directories ────────────────────────────────────────
# Create directories that need to survive across restarts.
RUN mkdir -p /app/tmp_raj_dev /app/session

# ── Environment variable defaults ─────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TEMP_DIR=/app/tmp_raj_dev \
    MAX_WORKERS=25 \
    MAX_RETRIES=5

# ── Security: run as non-root user ────────────────────────────────
# Principle of least privilege — bot does not need root access.
RUN addgroup --system rajdev \
    && adduser --system --ingroup rajdev --no-create-home rajdev \
    && chown -R rajdev:rajdev /app

# Ensure non-root user has absolute read/write access to the folders
RUN chmod -R 777 /app/tmp_raj_dev /app/session

USER rajdev

# ── Entrypoint ────────────────────────────────────────────────────
CMD ["python", "-u", "raj_dev_renamer_bot.py"]
