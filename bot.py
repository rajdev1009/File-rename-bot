"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              RAJ DEV — TELEGRAM FILE RENAMER BOT                            ║
║              Developer  : Raj Dev                                            ║
║              Telegram   : @raj_dev_01                                        ║
║              Build      : Production-Grade | Asyncio | Telethon              ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REQUIREMENTS FOR DEPLOYING ON CLOUD (Koyeb / Render / Railway / VPS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Runtime   : Python 3.10 or higher (3.11 recommended)
  Base Image: python:3.10-slim (Docker)

  Python Packages (see requirements.txt):
    - telethon==1.36.0      → Telegram MTProto client library
    - aiofiles==23.2.1      → Async disk I/O for temp file handling
    - cryptg (optional)     → C-extension for faster Telethon encryption

  Environment Variables (set in cloud dashboard — NEVER hardcode):
    ┌─────────────────┬──────────────────────────────────────────────────┐
    │ Variable Name   │ Description                                      │
    ├─────────────────┼──────────────────────────────────────────────────┤
    │ API_ID          │ Integer from https://my.telegram.org             │
    │ API_HASH        │ String  from https://my.telegram.org             │
    │ BOT_TOKEN       │ Bot token from @BotFather on Telegram            │
    │ CHANNEL_ID      │ Target channel as integer e.g. -1001234567890    │
    └─────────────────┴──────────────────────────────────────────────────┘

  Channel Permissions Required:
    - Bot must be an ADMIN of the target channel
    - "Post Messages" permission → ON  (for uploading renamed files)
    - "Delete Messages" permission → ON (for removing original files)

  Persistent Storage:
    - A writable volume/disk must be mounted at /app/tmp_raj_dev
      (Koyeb: Persistent Volume | Render: Disk | VPS: any writable path)
    - The Telethon session file (raj_dev_renamer_session.session) is
      written to the working directory — mount a persistent disk so the
      session survives container restarts and avoids repeated re-auth.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PROJECT FILE STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  raj-dev-renamer-bot/
  ├── raj_dev_renamer_bot.py          ← MAIN BOT (this file)
  ├── requirements.txt                ← Pinned Python dependencies
  ├── Dockerfile                      ← Container build instructions
  ├── .env                            ← Local-only secrets (DO NOT commit)
  ├── raj_dev_bot.log                 ← Auto-created runtime log file
  └── tmp_raj_dev/                    ← Auto-created temp download folder
      └── <uuid>.ext                  ← Collision-proof in-flight file chunks

  .env format (for local development only):
      API_ID=12345678
      API_HASH=abcdef1234567890abcdef1234567890
      BOT_TOKEN=123456789:AABBccDDeeFFggHHiiJJkkLLmmNNoo
      CHANNEL_ID=-1001234567890

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HOW THE CORE ASYNC QUEUE & PROCESS PIPELINE WORKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  STEP 0 — STARTUP
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  main() runs _run_integrity_check() → prints ASCII banner → reads env  │
  │  vars → creates asyncio.Semaphore(25) + asyncio.Queue(maxsize=500)     │
  │  → spawns 25 persistent _worker() coroutines as asyncio Tasks          │
  └─────────────────────────────────────────────────────────────────────────┘

  STEP 1 — EVENT CAPTURE (main thread, non-blocking)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Telethon fires @client.on(events.NewMessage) for every new post in    │
  │  the target channel. The handler filters out text-only and pure-photo  │
  │  messages, then calls await _queue.put(message) and returns instantly. │
  │  The event loop is NEVER blocked — the handler is a fast dispatcher.   │
  └─────────────────────────────────────────────────────────────────────────┘
             │
             ▼  asyncio.Queue  (max 500 items — backpressure cap)
  ┌──────────┴──────────────────────────────────────────────────────────────┐
  │  [ msg_1 ] [ msg_2 ] [ msg_3 ] ··· [ msg_N ]                          │
  └──────────┬──────────────────────────────────────────────────────────────┘
             │  25 workers pull concurrently
             ▼

  STEP 2 — WORKER POOL (25 persistent coroutines)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Each _worker() loops forever:                                          │
  │    message = await _queue.get()      ← suspends until item available   │
  │    async with _semaphore:            ← gates max 25 simultaneous ops   │
  │        await _process_file(client, message)                            │
  │    _queue.task_done()                                                   │
  │  Workers are NOT threads — they are cooperative coroutines sharing the  │
  │  single-threaded event loop. No GIL contention; all I/O is non-blocking│
  └─────────────────────────────────────────────────────────────────────────┘

  STEP 3 — _process_file() PIPELINE (per file)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  A) RESOLVE  → Extract original filename from document attributes or   │
  │               infer from MIME type.                                     │
  │                                                                         │
  │  B) BUILD    → Construct new name: "Raj Dev - <original>.<ext>"        │
  │               Generate uuid4-based unique temp path to avoid race      │
  │               conditions when 25 workers download simultaneously.       │
  │                                                                         │
  │  C) DOWNLOAD → client.download_media() streams up to 2 GB directly     │
  │               to the unique temp path. Retries up to 5× on failure.    │
  │               FloodWaitError → sleep(seconds + 2) then auto-resume.    │
  │               Exponential backoff (2^attempt) for other errors.         │
  │                                                                         │
  │  D) UPLOAD   → client.send_file() with force_document=True and         │
  │               file_name=new_name sends the renamed file back to the    │
  │               channel with caption "✅ Successfully Renamed by Raj Dev" │
  │               part_size_kb=512 ensures stability for large files.       │
  │                                                                         │
  │  E) DELETE   → client.delete_messages() removes the original un-named  │
  │               message from the channel immediately after upload.        │
  │                                                                         │
  │  F) CLEANUP  → Temp file erased from disk via _safe_delete_file()      │
  │               regardless of success or failure (called in finally).     │
  └─────────────────────────────────────────────────────────────────────────┘

  STEP 4 — GRACEFUL SHUTDOWN  (Ctrl+C or SIGTERM)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  main() catches KeyboardInterrupt / CancelledError → sends N None      │
  │  sentinel values into the queue (one per worker) → each worker exits   │
  │  its loop cleanly → asyncio.gather() waits for all → client.disconnect │
  └─────────────────────────────────────────────────────────────────────────┘

  CONCURRENCY SUMMARY:
    • Max simultaneous file operations : 25  (Semaphore)
    • Queue backpressure cap           : 500 messages
    • Max file size supported          : ~2 GB (Telegram Bot API limit)
    • FloodWait handling               : Automatic sleep + resume
    • Temp file collision risk         : Zero (uuid4 per download)
    • Thread usage                     : Zero (pure asyncio)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ─────────────────────────────────────────────────────────────────
# STANDARD LIBRARY IMPORTS
# ─────────────────────────────────────────────────────────────────
import os
import sys
import asyncio
import hashlib
import base64
import logging
import time
import uuid
import re
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# THIRD-PARTY IMPORTS
# ─────────────────────────────────────────────────────────────────
try:
    from telethon import TelegramClient, events
    from telethon.errors import (
        FloodWaitError,
        MessageDeleteForbiddenError,
        MessageNotModifiedError,
    )
    from telethon.tl.types import (
        MessageMediaDocument,
        MessageMediaPhoto,
    )
except ImportError:
    print("\n[FATAL] Telethon not installed. Run: pip install telethon\n")
    sys.exit(1)

try:
    import aiofiles
except ImportError:
    print("\n[FATAL] aiofiles not installed. Run: pip install aiofiles\n")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("raj_dev_bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("RajDevBot")

# ─────────────────────────────────────────────────────────────────
# ██████████████████████████████████████████████████████████████
#  INTEGRITY ENGINE — DO NOT MODIFY ANYTHING IN THIS SECTION
# ██████████████████████████████████████████████████████████████
# ─────────────────────────────────────────────────────────────────

# Developer identity stored as Base64-encoded strings.
# Altering these values will trigger an immediate fatal crash.
_DEV_NAME_B64   = b"UmFqIERldg=="           # "Raj Dev"
_DEV_TG_B64     = b"QHJhal9kZXZfMDE="       # "@raj_dev_01"

# SHA-256 reference checksums of the DECODED identity strings.
# These act as a tamper-proof seal.
# Generated via: hashlib.sha256("Raj Dev".encode()).hexdigest()
#            and hashlib.sha256("@raj_dev_01".encode()).hexdigest()
_DEV_NAME_SHA256 = "b036a790a298cf1e384234a29346ef00760880bea09c09d1f82f1c36d841db22"
_DEV_TG_SHA256   = "92860b13c4576cc10d5903abdda63ec8b46d0aec050ab05dceed4299893fb9a6"


def _sha256(text: str) -> str:
    """Return hex SHA-256 digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _decode_identity(b64_bytes: bytes) -> str:
    """Decode a Base64-encoded identity string."""
    return base64.b64decode(b64_bytes).decode("utf-8")


def _run_integrity_check() -> tuple[str, str]:
    """
    Decode and validate developer identity strings.
    On ANY mismatch → immediate fatal crash.
    Returns (dev_name, dev_tg) if valid.
    """
    try:
        dev_name = _decode_identity(_DEV_NAME_B64)
        dev_tg   = _decode_identity(_DEV_TG_B64)
    except Exception:
        _fatal_crash("Identity decoding failed.")

    # ── LAYER 1: SHA-256 Checksum Seal (ACTIVE) ───────────────────
    # Recompute live hashes from decoded strings and compare against
    # the hardcoded reference seals burned into this source file.
    # Any alteration to _DEV_NAME_B64 / _DEV_TG_B64 produces a
    # different decoded string → different hash → immediate crash.
    live_name_hash = _sha256(dev_name)
    live_tg_hash   = _sha256(dev_tg)

    if live_name_hash != _DEV_NAME_SHA256:
        _fatal_crash("Developer name checksum mismatch. Code has been tampered.")

    if live_tg_hash != _DEV_TG_SHA256:
        _fatal_crash("Developer handle checksum mismatch. Code has been tampered.")

    # ── LAYER 2: Plaintext Identity Guard (ACTIVE) ────────────────
    # Independent secondary check. Even if hash constants were altered,
    # this layer catches any decoded-value deviation.
    if dev_name != "Raj Dev" or dev_tg != "@raj_dev_01":
        _fatal_crash("Identity string mismatch. Core License Violated.")

    return dev_name, dev_tg


def _fatal_crash(reason: str = ""):
    """Hard-kill the process on integrity violation."""
    msg = (
        "\n"
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║  FATAL ERROR: Unauthorized Code Modification Detected.       ║\n"
        "║  Core License Violated.                                      ║\n"
        f"║  Reason: {reason:<52}║\n"
        "╚══════════════════════════════════════════════════════════════╝\n"
    )
    print(msg, file=sys.stderr, flush=True)
    log.critical("INTEGRITY VIOLATION: %s", reason)
    os._exit(1)   # immediate, no-cleanup exit


# ─────────────────────────────────────────────────────────────────
# ASCII DEPLOYMENT BANNER
# ─────────────────────────────────────────────────────────────────

_BANNER_TEMPLATE = r"""
\033[1;36m
 ██████╗  █████╗      ██╗    ██████╗ ███████╗██╗   ██╗
 ██╔══██╗██╔══██╗     ██║    ██╔══██╗██╔════╝██║   ██║
 ██████╔╝███████║     ██║    ██║  ██║█████╗  ██║   ██║
 ██╔══██╗██╔══██║██   ██║    ██║  ██║██╔══╝  ╚██╗ ██╔╝
 ██║  ██║██║  ██║╚█████╔╝    ██████╔╝███████╗ ╚████╔╝
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚════╝     ╚═════╝ ╚══════╝  ╚═══╝
\033[0m
\033[1;33m  ┌─────────────────────────────────────────────────────┐
  │  Developer  :  {dev_name:<36}│
  │  Telegram   :  {dev_tg:<36}│
  │  Status     :  \033[1;32mAuthorized ✅\033[1;33m                              │
  │  Build      :  Production-Grade Asyncio Renamer Bot  │
  └─────────────────────────────────────────────────────┘\033[0m
"""


def _print_banner(dev_name: str, dev_tg: str):
    """Print the stylized ASCII deployment banner."""
    banner = _BANNER_TEMPLATE.replace("{dev_name}", dev_name).replace("{dev_tg}", dev_tg)
    # Render ANSI escape sequences properly
    banner = banner.encode().decode("unicode_escape") if "\\033" in banner else banner
    print(banner, flush=True)


# ─────────────────────────────────────────────────────────────────
# BOT CONFIGURATION — Loaded from Environment Variables
# Set these in your cloud dashboard (Koyeb/Render) or a local .env
# NEVER hardcode secrets into source code.
# ─────────────────────────────────────────────────────────────────

def _get_env_int(key: str, fallback: int = 0) -> int:
    """Read an environment variable and cast it to int, with a fallback."""
    val = os.environ.get(key, "").strip()
    try:
        return int(val)
    except (ValueError, TypeError):
        return fallback

API_ID     : int = _get_env_int("API_ID")
API_HASH   : str = os.environ.get("API_HASH",   "").strip()
BOT_TOKEN  : str = os.environ.get("BOT_TOKEN",  "").strip()
CHANNEL_ID : int = _get_env_int("CHANNEL_ID")

# Operational tunables
MAX_CONCURRENT_TASKS: int  = int(os.environ.get("MAX_WORKERS", "25"))
TEMP_DIR            : Path = Path(os.environ.get("TEMP_DIR", "./tmp_raj_dev"))
MAX_RETRIES         : int  = int(os.environ.get("MAX_RETRIES", "5"))

# ─────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────────────────────────

_semaphore: asyncio.Semaphore | None = None   # Concurrency gate
_queue:     asyncio.Queue | None     = None   # Incoming file queue
_dev_name:  str = ""
_dev_tg:    str = ""

# ─────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """Strip characters that are illegal in filenames across OSes."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.strip(". ")
    return name or "unnamed"


def _build_new_filename(original_name: str) -> str:
    """
    Apply the renaming convention:
        Raj Dev - [Original_File_Name].[ext]
    """
    stem, _, ext = original_name.rpartition(".")
    if not stem:          # filename had no extension
        stem = original_name
        ext  = ""
    clean_stem = _sanitize_filename(stem)
    new_name   = f"{_dev_name} - {clean_stem}"
    return f"{new_name}.{ext}" if ext else new_name


def _unique_temp_path(original_name: str) -> Path:
    """Generate a collision-proof temp file path."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    uid      = uuid.uuid4().hex
    _, _, ext = original_name.rpartition(".")
    suffix   = f".{ext}" if ext else ""
    return TEMP_DIR / f"{uid}{suffix}"


async def _safe_delete_file(path: Path):
    """Delete a local temp file, ignoring errors."""
    try:
        if path.exists():
            path.unlink()
    except Exception as exc:
        log.warning("Could not delete temp file %s: %s", path, exc)


# ─────────────────────────────────────────────────────────────────
# CORE PROCESSING LOGIC
# ─────────────────────────────────────────────────────────────────

async def _process_file(client: TelegramClient, message) -> bool:
    """
    Full pipeline for a single file message:
      1. Resolve original filename & extension.
      2. Download to unique temp path (supports up to 2 GB via streaming).
      3. Upload with new name + attribution caption.
      4. Delete the original channel message.
      5. Purge local temp file.

    Returns True on success, False on unrecoverable failure.
    """
    media = message.media
    if not media:
        return False

    # ── Resolve original filename ──────────────────────────────
    original_name = "file"
    try:
        if hasattr(media, "document") and media.document:
            doc = media.document
            for attr in doc.attributes:
                if hasattr(attr, "file_name") and attr.file_name:
                    original_name = attr.file_name
                    break
            else:
                # Guess extension from MIME
                mime = getattr(doc, "mime_type", "")
                ext  = mime.split("/")[-1] if "/" in mime else "bin"
                original_name = f"document.{ext}"
        elif hasattr(media, "photo"):
            original_name = "photo.jpg"
    except Exception as exc:
        log.warning("msg_id=%d  Could not resolve filename: %s", message.id, exc)

    new_name   = _build_new_filename(original_name)
    temp_path  = _unique_temp_path(original_name)
    caption    = (
        f"✅ Successfully Renamed by {_dev_name} ({_dev_tg})"
    )

    log.info("msg_id=%-8d  [START]  %s  →  %s", message.id, original_name, new_name)

    # ── Download ───────────────────────────────────────────────
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client.download_media(message, file=str(temp_path))
            log.info("msg_id=%-8d  [DOWNLOADED]  attempt=%d", message.id, attempt)
            break
        except FloodWaitError as fwe:
            log.warning(
                "msg_id=%-8d  FloodWait %ds on download (attempt %d/%d)",
                message.id, fwe.seconds, attempt, MAX_RETRIES,
            )
            await asyncio.sleep(fwe.seconds + 2)
        except Exception as exc:
            log.error(
                "msg_id=%-8d  Download error (attempt %d/%d): %s",
                message.id, attempt, MAX_RETRIES, exc,
            )
            await asyncio.sleep(2 ** attempt)   # exponential back-off
    else:
        log.error("msg_id=%-8d  [FAILED]  Max retries reached on download.", message.id)
        await _safe_delete_file(temp_path)
        return False

    if not temp_path.exists() or temp_path.stat().st_size == 0:
        log.error("msg_id=%-8d  [FAILED]  Downloaded file is empty/missing.", message.id)
        await _safe_delete_file(temp_path)
        return False

    # ── Upload ─────────────────────────────────────────────────
    uploaded = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # force_document=True preserves file integrity for all types
            await client.send_file(
                CHANNEL_ID,
                file=str(temp_path),
                caption=caption,
                attributes=[],           # Telethon infers from file
                force_document=True,
                file_name=new_name,
                part_size_kb=512,        # 512 KB parts → stable for 2 GB files
            )
            log.info(
                "msg_id=%-8d  [UPLOADED]  %s  (attempt %d)",
                message.id, new_name, attempt,
            )
            uploaded = True
            break
        except FloodWaitError as fwe:
            log.warning(
                "msg_id=%-8d  FloodWait %ds on upload (attempt %d/%d)",
                message.id, fwe.seconds, attempt, MAX_RETRIES,
            )
            await asyncio.sleep(fwe.seconds + 2)
        except Exception as exc:
            log.error(
                "msg_id=%-8d  Upload error (attempt %d/%d): %s",
                message.id, attempt, MAX_RETRIES, exc,
            )
            await asyncio.sleep(2 ** attempt)

    await _safe_delete_file(temp_path)   # always purge local copy

    if not uploaded:
        log.error("msg_id=%-8d  [FAILED]  Max retries reached on upload.", message.id)
        return False

    # ── Delete original message ───────────────────────────────
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client.delete_messages(CHANNEL_ID, [message.id])
            log.info("msg_id=%-8d  [DELETED]  Original message removed.", message.id)
            break
        except FloodWaitError as fwe:
            await asyncio.sleep(fwe.seconds + 2)
        except (MessageDeleteForbiddenError, Exception) as exc:
            log.warning(
                "msg_id=%-8d  Delete error (attempt %d/%d): %s",
                message.id, attempt, MAX_RETRIES, exc,
            )
            await asyncio.sleep(2 ** attempt)

    log.info("msg_id=%-8d  [DONE]  Pipeline complete.", message.id)
    return True


# ─────────────────────────────────────────────────────────────────
# WORKER POOL
# ─────────────────────────────────────────────────────────────────

async def _worker(client: TelegramClient, worker_id: int):
    """
    Persistent async worker.
    Pulls messages from the queue, acquires semaphore, processes.
    Runs forever until the queue receives a None sentinel.
    """
    log.debug("Worker-%d started.", worker_id)
    while True:
        message = await _queue.get()
        if message is None:             # Shutdown sentinel
            _queue.task_done()
            break
        async with _semaphore:
            try:
                await _process_file(client, message)
            except Exception as exc:
                log.exception(
                    "Worker-%d  Unhandled exception for msg_id=%d: %s",
                    worker_id, message.id, exc,
                )
            finally:
                _queue.task_done()
    log.debug("Worker-%d exiting.", worker_id)


# ─────────────────────────────────────────────────────────────────
# TELETHON EVENT HANDLER
# ─────────────────────────────────────────────────────────────────

def _register_handlers(client: TelegramClient):
    """Attach new-message handler scoped to the target channel."""

    @client.on(events.NewMessage(chats=CHANNEL_ID))
    async def _on_new_message(event):
        message = event.message
        # Accept: documents, videos, audio.  Skip text-only & photos.
        if not message.media:
            return
        if isinstance(message.media, MessageMediaPhoto):
            return   # skip pure photos (rename doesn't apply)

        log.info(
            "msg_id=%-8d  Queued  (queue_size=%d)",
            message.id, _queue.qsize(),
        )
        await _queue.put(message)

    log.info("Event handler registered for channel_id=%d", CHANNEL_ID)


# ─────────────────────────────────────────────────────────────────
# STARTUP & MAIN
# ─────────────────────────────────────────────────────────────────

async def _startup_checks():
    """Validate that all required environment variables are loaded."""
    errors = []
    if not API_ID or API_ID == 0:
        errors.append("API_ID is missing or zero. Set the API_ID environment variable.")
    if not API_HASH:
        errors.append("API_HASH is missing. Set the API_HASH environment variable.")
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is missing. Set the BOT_TOKEN environment variable.")
    if not CHANNEL_ID or CHANNEL_ID == 0:
        errors.append("CHANNEL_ID is missing or zero. Set the CHANNEL_ID environment variable.")
    if errors:
        for e in errors:
            log.error("CONFIG ERROR: %s", e)
        log.error(
            "One or more required environment variables are not set.\n"
            "  → Set them in your cloud dashboard (Koyeb/Render) or local .env file.\n"
            "  → Required: API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID"
        )
        sys.exit(1)


async def main():
    global _semaphore, _queue, _dev_name, _dev_tg

    # ── 1. Integrity check (must be first) ─────────────────────
    _dev_name, _dev_tg = _run_integrity_check()

    # ── 2. Deployment banner ────────────────────────────────────
    _print_banner(_dev_name, _dev_tg)
    print("Hello, I am Raj. I am now live! 🚀", flush=True)
    log.info("Integrity check passed. Developer: %s (%s)", _dev_name, _dev_tg)

    # ── 3. Config sanity ────────────────────────────────────────
    await _startup_checks()

    # ── 4. Ensure temp directory ─────────────────────────────────
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # ── 5. Concurrency primitives ────────────────────────────────
    _semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    _queue     = asyncio.Queue(maxsize=500)   # backpressure cap

    # ── 6. Telethon client ───────────────────────────────────────
    client = TelegramClient(
        "raj_dev_renamer_session",
        API_ID,
        API_HASH,
        # Production-grade connection settings
        connection_retries=10,
        retry_delay=5,
        request_retries=5,
        flood_sleep_threshold=60,
        device_model="RajDevBot/Production",
        system_version="Linux",
        app_version="1.0.0",
    )

    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    log.info("Bot connected as: @%s (id=%d)", me.username, me.id)

    # ── 7. Register event handler ────────────────────────────────
    _register_handlers(client)

    # ── 8. Spawn persistent workers ──────────────────────────────
    workers = [
        asyncio.create_task(_worker(client, i))
        for i in range(MAX_CONCURRENT_TASKS)
    ]
    log.info("Spawned %d async workers.", MAX_CONCURRENT_TASKS)
    log.info("Bot is live. Monitoring channel_id=%d  Press Ctrl+C to stop.", CHANNEL_ID)

    # ── 9. Run until interrupted ─────────────────────────────────
    try:
        await client.run_until_disconnected()
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("Shutdown signal received.")
    finally:
        # Graceful shutdown: send sentinels to all workers
        log.info("Sending shutdown sentinels to %d workers...", MAX_CONCURRENT_TASKS)
        for _ in workers:
            await _queue.put(None)
        await asyncio.gather(*workers, return_exceptions=True)
        await client.disconnect()
        log.info("Bot disconnected. Goodbye from %s (%s)!", _dev_name, _dev_tg)


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except Exception as exc:
        log.exception("Unhandled top-level exception: %s", exc)
        sys.exit(1)
