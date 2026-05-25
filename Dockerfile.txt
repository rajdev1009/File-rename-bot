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
# Install build tools needed for cryptg (C-extension) and clean up
# apt cache in the same layer to keep image size minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────
# Copy requirements first so Docker can cache this layer separately
# from the source code. Rebuilds only when requirements.txt changes.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────
COPY raj_dev_renamer_bot.py .

# ── Persistent directories ────────────────────────────────────────
# Create directories that need to survive across restarts.
# On Koyeb/Render, mount a persistent volume to /app/tmp_raj_dev
# and /app/session so the Telethon .session file is not lost on
# container redeploys (which would force re-authentication).
RUN mkdir -p /app/tmp_raj_dev /app/session

# ── Environment variable defaults ─────────────────────────────────
# These are NON-SECRET defaults only. Actual secrets (API_ID,
# API_HASH, BOT_TOKEN, CHANNEL_ID) MUST be injected at runtime
# via the cloud dashboard's environment variable settings.
# NEVER put real tokens in the Dockerfile.
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

USER rajdev

# ── Health / metadata ─────────────────────────────────────────────
# Telegram bots don't expose HTTP ports, so no EXPOSE directive needed.
# Koyeb/Render will detect the process as healthy if it stays running.

# ── Entrypoint ────────────────────────────────────────────────────
CMD ["python", "-u", "raj_dev_renamer_bot.py"]
