"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          RAJ DEV — AUTO CAPTION CLEANER BOT                                 ║
║          Developer  : Raj Dev  |  Telegram : @raj_dev_01                    ║
║          Function   : Removes old captions/links, adds Raj Dev branding     ║
╚══════════════════════════════════════════════════════════════════════════════╝

SETUP:
  1. pip install telethon
  2. Set environment variables: API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID
  3. Add bot as Admin in channel (Post + Delete Messages permissions)
  4. python raj_dev_caption_bot.py

HOW IT WORKS:
  - Any file posted in the channel → bot deletes old message → reposts
    same file with clean caption (Raj Dev branding only, no old links/text)
  - /rename command: reply to any file → bot reposts with clean caption
  - Works on: documents, videos, audio, zip, apk — any file type
"""

import os
import sys
import asyncio
import hashlib
import base64
import logging
import uuid
import re
from pathlib import Path

# ── Dependency check ─────────────────────────────────────────────
try:
    from telethon import TelegramClient, events, Button
    from telethon.errors import FloodWaitError, MessageDeleteForbiddenError
    from telethon.tl.types import (
        MessageMediaDocument,
        MessageMediaPhoto,
        DocumentAttributeFilename,
        DocumentAttributeVideo,
        DocumentAttributeAudio,
    )
except ImportError:
    print("\n[FATAL] Run: pip install telethon\n")
    sys.exit(1)

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("raj_dev_caption_bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("RajDevCaptionBot")

# ══════════════════════════════════════════════════════════════════
#  INTEGRITY ENGINE  —  DO NOT MODIFY
# ══════════════════════════════════════════════════════════════════

_DEV_NAME_B64    = b"UmFqIERldg=="
_DEV_TG_B64      = b"QHJhal9kZXZfMDE="
_DEV_NAME_SHA256 = "b036a790a298cf1e384234a29346ef00760880bea09c09d1f82f1c36d841db22"
_DEV_TG_SHA256   = "92860b13c4576cc10d5903abdda63ec8b46d0aec050ab05dceed4299893fb9a6"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _fatal_crash(reason: str = ""):
    print(
        f"\n╔══════════════════════════════════════════════════════╗\n"
        f"║  FATAL ERROR: Unauthorized Code Modification.        ║\n"
        f"║  Core License Violated.                              ║\n"
        f"║  Reason: {reason:<44}║\n"
        f"╚══════════════════════════════════════════════════════╝\n",
        file=sys.stderr, flush=True,
    )
    os._exit(1)


def _run_integrity_check() -> tuple:
    try:
        dev_name = base64.b64decode(_DEV_NAME_B64).decode()
        dev_tg   = base64.b64decode(_DEV_TG_B64).decode()
    except Exception:
        _fatal_crash("Identity decode failed.")
    if _sha256(dev_name) != _DEV_NAME_SHA256:
        _fatal_crash("Name checksum mismatch.")
    if _sha256(dev_tg) != _DEV_TG_SHA256:
        _fatal_crash("Handle checksum mismatch.")
    if dev_name != "Raj Dev" or dev_tg != "@raj_dev_01":
        _fatal_crash("Identity string mismatch.")
    return dev_name, dev_tg

# ══════════════════════════════════════════════════════════════════
#  ASCII BANNER
# ══════════════════════════════════════════════════════════════════

def _print_banner(dev_name: str, dev_tg: str):
    C = "\033[1;36m"; Y = "\033[1;33m"; G = "\033[1;32m"; R = "\033[0m"
    print(f"""
{C} ██████╗  █████╗      ██╗    ██████╗ ███████╗██╗   ██╗
 ██╔══██╗██╔══██╗     ██║    ██╔══██╗██╔════╝██║   ██║
 ██████╔╝███████║     ██║    ██║  ██║█████╗  ██║   ██║
 ██╔══██╗██╔══██║██   ██║    ██║  ██║██╔══╝  ╚██╗ ██╔╝
 ██║  ██║██║  ██║╚█████╔╝    ██████╔╝███████╗ ╚████╔╝
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚════╝     ╚═════╝ ╚══════╝  ╚═══╝{R}
{Y}  ┌──────────────────────────────────────────────────────┐
  │  Developer  : {dev_name:<37}│
  │  Telegram   : {dev_tg:<37}│
  │  Status     : {G}Authorized ✅{Y}                               │
  │  Mode       : Auto Caption Cleaner Bot                │
  └──────────────────────────────────────────────────────┘{R}
""", flush=True)
    print("Hello, I am Raj. I am now live! 🚀\n", flush=True)

# ══════════════════════════════════════════════════════════════════
#  CONFIGURATION  —  from environment variables
# ══════════════════════════════════════════════════════════════════

def _env_int(key: str) -> int:
    try:
        return int(os.environ.get(key, "0").strip())
    except ValueError:
        return 0

API_ID     : int  = _env_int("API_ID")
API_HASH   : str  = os.environ.get("API_HASH",   "").strip()
BOT_TOKEN  : str  = os.environ.get("BOT_TOKEN",  "").strip()
CHANNEL_ID : int  = _env_int("CHANNEL_ID")
MAX_WORKERS: int  = int(os.environ.get("MAX_WORKERS", "10"))
MAX_RETRIES: int  = int(os.environ.get("MAX_RETRIES", "5"))
TEMP_DIR   : Path = Path(os.environ.get("TEMP_DIR", "./tmp_raj_dev"))

# ── Global state ──────────────────────────────────────────────────
_semaphore : asyncio.Semaphore | None = None
_queue     : asyncio.Queue | None     = None
_dev_name  : str = ""
_dev_tg    : str = ""

# ══════════════════════════════════════════════════════════════════
#  CAPTION BUILDER
# ══════════════════════════════════════════════════════════════════

def _build_clean_caption(original_filename: str) -> str:
    """
    Returns a clean branded caption.
    ALL old text, links, usernames from original caption are discarded.
    """
    return (
        f"🎬 **{original_filename}**\n\n"
        f"📤 Uploaded by: **{_dev_name}**\n"
        f"📢 Channel: {_dev_tg}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

# ══════════════════════════════════════════════════════════════════
#  FILE INFO EXTRACTOR
# ══════════════════════════════════════════════════════════════════

def _extract_file_info(media) -> tuple:
    """
    Returns (filename, mime_type, file_size_bytes, doc_object)
    Works for any document type: video, audio, zip, apk, pdf, etc.
    """
    if not (media and hasattr(media, "document") and media.document):
        return None, None, 0, None

    doc       = media.document
    mime      = getattr(doc, "mime_type", "application/octet-stream")
    size      = getattr(doc, "size", 0)
    filename  = None

    for attr in doc.attributes:
        if hasattr(attr, "file_name") and attr.file_name:
            filename = attr.file_name
            break

    if not filename:
        ext      = mime.split("/")[-1] if "/" in mime else "bin"
        filename = f"file.{ext}"

    return filename, mime, size, doc


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.2f} GB"

# ══════════════════════════════════════════════════════════════════
#  CORE PIPELINE  —  Download → Repost with clean caption → Delete original
# ══════════════════════════════════════════════════════════════════

async def _process_message(client: TelegramClient, message, notify_chat=None, notify_msg_id=None):
    """
    Full pipeline:
      1. Extract filename from document (no download yet)
      2. Build clean Raj Dev caption  (old caption/links DISCARDED)
      3. Download file to temp path
      4. Re-upload with clean caption
      5. Delete original message
      6. Clean up temp file

    notify_chat / notify_msg_id: if set, bot edits that message with status updates.
    """
    filename, mime, size, doc = _extract_file_info(message.media)
    if not filename:
        return False

    clean_caption = _build_clean_caption(filename)
    size_str      = _human_size(size)

    log.info("msg_id=%-8d  Processing: %s  (%s)", message.id, filename, size_str)

    # ── Notify: starting ─────────────────────────────────────────
    status_msg = None
    if notify_chat and notify_msg_id:
        try:
            status_msg = await client.send_message(
                notify_chat,
                f"⏳ Processing `{filename}` ({size_str})...",
                reply_to=notify_msg_id,
            )
        except Exception:
            pass

    # ── Temp path ─────────────────────────────────────────────────
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    _, _, ext = filename.rpartition(".")
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}.{ext}"

    # ── Download ──────────────────────────────────────────────────
    downloaded = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client.download_media(message, file=str(temp_path))
            if temp_path.exists() and temp_path.stat().st_size > 0:
                downloaded = True
                log.info("msg_id=%-8d  Downloaded (%s)", message.id, size_str)
                break
        except FloodWaitError as e:
            log.warning("msg_id=%-8d  FloodWait %ds", message.id, e.seconds)
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            log.error("msg_id=%-8d  Download attempt %d failed: %s", message.id, attempt, e)
            await asyncio.sleep(2 ** attempt)

    if not downloaded:
        if status_msg:
            await status_msg.edit(f"❌ Failed to download `{filename}`.")
        _try_del_local(temp_path)
        return False

    # ── Re-upload with CLEAN caption ──────────────────────────────
    uploaded = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client.send_file(
                CHANNEL_ID,
                file=str(temp_path),
                caption=clean_caption,
                force_document=True,
                file_name=filename,          # keep original filename unchanged
                parse_mode="md",
                part_size_kb=512,
            )
            uploaded = True
            log.info("msg_id=%-8d  Uploaded with clean caption.", message.id)
            break
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            log.error("msg_id=%-8d  Upload attempt %d failed: %s", message.id, attempt, e)
            await asyncio.sleep(2 ** attempt)

    _try_del_local(temp_path)

    if not uploaded:
        if status_msg:
            await status_msg.edit(f"❌ Upload failed for `{filename}`.")
        return False

    # ── Delete original message ───────────────────────────────────
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client.delete_messages(CHANNEL_ID, [message.id])
            log.info("msg_id=%-8d  Original deleted.", message.id)
            break
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            log.warning("msg_id=%-8d  Delete attempt %d: %s", message.id, attempt, e)
            await asyncio.sleep(2 ** attempt)

    # ── Update status message ─────────────────────────────────────
    if status_msg:
        try:
            await status_msg.edit(
                f"✅ **Done!**\n"
                f"📄 `{filename}`\n"
                f"📦 Size: {size_str}\n"
                f"🏷️ Caption cleaned & Raj Dev branding added."
            )
        except Exception:
            pass

    log.info("msg_id=%-8d  [COMPLETE] %s", message.id, filename)
    return True


def _try_del_local(path: Path):
    try:
        if path and path.exists():
            path.unlink()
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════
#  WORKER POOL
# ══════════════════════════════════════════════════════════════════

async def _worker(client: TelegramClient, wid: int):
    log.debug("Worker-%d ready.", wid)
    while True:
        item = await _queue.get()
        if item is None:
            _queue.task_done()
            break
        message, notify_chat, notify_msg_id = item
        async with _semaphore:
            try:
                await _process_message(client, message, notify_chat, notify_msg_id)
            except Exception as e:
                log.exception("Worker-%d error msg_id=%d: %s", wid, message.id, e)
            finally:
                _queue.task_done()
    log.debug("Worker-%d exiting.", wid)

# ══════════════════════════════════════════════════════════════════
#  COMMAND & EVENT HANDLERS
# ══════════════════════════════════════════════════════════════════

def _register_handlers(client: TelegramClient):

    # ── /start ────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^/start$"))
    async def cmd_start(event):
        sender = await event.get_sender()
        name   = getattr(sender, "first_name", "there") or "there"
        await event.reply(
            f"👋 **Hello {name}! Welcome.**\n\n"
            f"I am **{_dev_name} Caption Bot**\n"
            f"Telegram: {_dev_tg}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**What I do:**\n"
            f"📌 Remove all old captions, links & usernames\n"
            f"📌 Add clean **Raj Dev** branding to every file\n"
            f"📌 Works on any file — video, audio, zip, apk, pdf\n\n"
            f"Type /help to see all commands.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        log.info("/start from %s (id=%d)", name, sender.id)

    # ── /raj ──────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^/raj$"))
    async def cmd_raj(event):
        await event.reply(
            f"👨‍💻 **Developer Info**\n\n"
            f"🔹 Name    : **{_dev_name}**\n"
            f"🔹 Telegram: **{_dev_tg}**\n"
            f"🔹 Role    : Bot Developer & Owner\n"
            f"🔹 Build   : Auto Caption Cleaner Bot\n\n"
            f"⚡ Powered by Telethon + Asyncio\n"
            f"🔒 Integrity-locked. Tamper = crash."
        )

    # ── /help ─────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^/help$"))
    async def cmd_help(event):
        await event.reply(
            f"📖 **{_dev_name} Caption Bot — Help**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**📋 Commands:**\n\n"
            f"▶️ /start\n"
            f"   Bot ka welcome message\n\n"
            f"▶️ /help\n"
            f"   Yeh help message\n\n"
            f"▶️ /raj\n"
            f"   Developer info dekhna\n\n"
            f"▶️ /clean\n"
            f"   _(Channel mein file ko reply karke)_\n"
            f"   Us file ka caption clean karo manually\n\n"
            f"▶️ /status\n"
            f"   Bot ka current status aur queue info\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**⚙️ Auto Mode (no command needed):**\n\n"
            f"Bas apne channel mein koi bhi file post karo.\n"
            f"Bot automatically:\n"
            f"  ✅ Purana caption/link/text hatayega\n"
            f"  ✅ File ka naam wahi rakhega\n"
            f"  ✅ Raj Dev branding add karega\n"
            f"  ✅ Original message delete karega\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**🔐 Permissions needed (bot must be Admin):**\n"
            f"  • Post Messages ✅\n"
            f"  • Delete Messages ✅\n\n"
            f"**📞 Support:** {_dev_tg}"
        )

    # ── /status ───────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^/status$"))
    async def cmd_status(event):
        q_size = _queue.qsize() if _queue else 0
        await event.reply(
            f"📊 **Bot Status**\n\n"
            f"🟢 Status     : **Live & Running**\n"
            f"👷 Workers    : {MAX_WORKERS} async\n"
            f"📥 Queue size : {q_size} pending\n"
            f"📡 Channel    : `{CHANNEL_ID}`\n"
            f"👤 Developer  : {_dev_name} ({_dev_tg})"
        )

    # ── /clean — reply to a file in channel ───────────────────────
    @client.on(events.NewMessage(pattern=r"^/clean$", chats=CHANNEL_ID))
    async def cmd_clean(event):
        if not event.message.reply_to_msg_id:
            await event.reply(
                "⚠️ Kisi file ko **reply** karke /clean likho.\n"
                "Example: channel mein file pe reply karo → /clean"
            )
            return
        try:
            target = await client.get_messages(CHANNEL_ID, ids=event.message.reply_to_msg_id)
        except Exception as e:
            await event.reply(f"❌ Message fetch error: {e}")
            return
        if not target or not target.media:
            await event.reply("⚠️ Replied message mein koi file nahi hai.")
            return
        filename, _, _, _ = _extract_file_info(target.media)
        if not filename:
            await event.reply("⚠️ Is message mein koi document nahi mila.")
            return
        # Delete the /clean command to keep channel clean
        try:
            await client.delete_messages(CHANNEL_ID, [event.message.id])
        except Exception:
            pass
        await _queue.put((target, None, None))
        log.info("/clean queued msg_id=%d (%s)", target.id, filename)

    # ── Auto mode: new file in channel ────────────────────────────
    @client.on(events.NewMessage(chats=CHANNEL_ID))
    async def on_channel_file(event):
        msg = event.message
        # Skip if no media or it's a photo
        if not msg.media or isinstance(msg.media, MessageMediaPhoto):
            return
        # Skip if already processed by this bot (caption contains our brand)
        cap = msg.message or ""
        if f"Uploaded by: **{_dev_name}**" in cap or f"Uploaded by: {_dev_name}" in cap:
            return
        filename, _, _, _ = _extract_file_info(msg.media)
        if not filename:
            return
        log.info("msg_id=%-8d  Auto-queued: %s (queue=%d)", msg.id, filename, _queue.qsize())
        await _queue.put((msg, None, None))

    log.info("All handlers registered: /start /raj /help /clean /status + auto-mode")

# ══════════════════════════════════════════════════════════════════
#  HEALTH SERVER  (for Koyeb / Render health checks)
# ══════════════════════════════════════════════════════════════════

async def _health_server():
    port = int(os.environ.get("PORT", "8000"))
    async def _handle(r, w):
        try:
            await r.read(1024)
            w.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK")
            await w.drain()
        except Exception:
            pass
        finally:
            try: w.close(); await w.wait_closed()
            except Exception: pass
    srv = await asyncio.start_server(_handle, "0.0.0.0", port)
    log.info("Health server on port %d", port)
    async with srv:
        await srv.serve_forever()

# ══════════════════════════════════════════════════════════════════
#  STARTUP CHECKS
# ══════════════════════════════════════════════════════════════════

async def _startup_checks():
    errors = []
    if not API_ID:   errors.append("API_ID missing")
    if not API_HASH: errors.append("API_HASH missing")
    if not BOT_TOKEN:errors.append("BOT_TOKEN missing")
    if not CHANNEL_ID: errors.append("CHANNEL_ID missing")
    if errors:
        for e in errors: log.error("CONFIG: %s", e)
        log.error("Set environment variables and restart.")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════
#  BOT RUNNER
# ══════════════════════════════════════════════════════════════════

async def _run_bot():
    global _semaphore, _queue

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    _semaphore = asyncio.Semaphore(MAX_WORKERS)
    _queue     = asyncio.Queue(maxsize=200)

    client = TelegramClient(
        "raj_dev_caption_session",
        API_ID, API_HASH,
        connection_retries=10,
        retry_delay=5,
        flood_sleep_threshold=60,
        device_model="RajDevCaptionBot/1.0",
        system_version="Linux",
        app_version="1.0.0",
    )

    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    log.info("Connected as: @%s (id=%d)", me.username, me.id)

    _register_handlers(client)

    workers = [asyncio.create_task(_worker(client, i)) for i in range(MAX_WORKERS)]
    log.info("Spawned %d workers. Monitoring channel_id=%d", MAX_WORKERS, CHANNEL_ID)

    try:
        await client.run_until_disconnected()
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("Shutdown signal.")
    finally:
        for _ in workers: await _queue.put(None)
        await asyncio.gather(*workers, return_exceptions=True)
        await client.disconnect()
        log.info("Disconnected. Bye from %s!", _dev_name)

# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

async def main():
    global _dev_name, _dev_tg
    _dev_name, _dev_tg = _run_integrity_check()
    _print_banner(_dev_name, _dev_tg)
    log.info("Integrity OK. Developer: %s (%s)", _dev_name, _dev_tg)
    await _startup_checks()
    await asyncio.gather(
        _health_server(),
        _run_bot(),
        return_exceptions=False,
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log.exception("Fatal: %s", e)
        sys.exit(1)
