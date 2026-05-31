# RAJ DEV — Auto Caption Cleaner Bot (Multi-Lang & Thumb)
# Developer: Raj Dev (@raj_dev_01)
FROM python:3.10-slim

LABEL maintainer="Raj Dev <@raj_dev_01>"
LABEL description="Auto Caption Cleaner Bot"

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libffi-dev libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY utils.py .

RUN mkdir -p /app/tmp_raj_dev /app/session

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TEMP_DIR=/app/tmp_raj_dev \
    MAX_WORKERS=10 \
    MAX_RETRIES=5 \
    PORT=7860

RUN addgroup --system rajdev \
    && adduser --system --ingroup rajdev --no-create-home rajdev \
    && chown -R rajdev:rajdev /app

USER rajdev

CMD ["python", "-u", "bot.py"]
