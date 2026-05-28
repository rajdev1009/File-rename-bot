"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          RAJ DEV — AUTO CAPTION CLEANER BOT (ZERO DOWNLOAD)                 ║
║          Developer  : Raj Dev  |  Telegram : @raj_dev_01                    ║
║          Function   : Removes old captions/links, adds Raj Dev branding     ║
╚══════════════════════════════════════════════════════════════════════════════╝
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
  │  Mode       : Auto Caption Cleaner Bot (Zero-DL)      │
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

# ── Global state ──────────────────────────────────────────────────
_semaphore : asyncio.Semaphore | None = None
_queue     : asyncio.Queue | None     = None
_dev_name  : str = ""
_dev_tg    : str = ""

# ══════════════════════════════════════════════════════════════════
#  CAPTION BUILDER
# ══════════════════════════════════════════════════════════════════

def _build_clean_caption(original_filename: str, size_str: str) -> str:
    """
    Returns a clean branded caption.
    ALL old text, links, usernames from original caption AND filename are discarded.
    """
    # 1. Filename mein agar koi link ya @username hai toh hatao
    clean_name = re.sub(r'@[a-zA-Z0-9_]+', '', original_filename)
    clean_name = re.sub(r'https?://\S+|t\.me/\S+', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'[_\-]+', ' ', clean_name).strip()
    
    if not clean_name:
        clean_name = original_filename

    # 2. Final clean caption format
    return (
        f"🎬 **{clean_name}**\n\n"
        f"📦 **Size:** {size_str}\n\n"
        f"📤 Uploaded by: **{_dev_name}**\n"
        f"📢 Channel: {_dev_tg}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

# ══════════════════════════════════════════════════════════════════
#  FILE INFO EXTRACTOR
# ══════════════════════════════════════════════════════════════════

def _extract_file_info(media) -> tuple:
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
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.2f} GB"

# ══════════════════════════════════════════════════════════════════
#  CORE PIPELINE  — ZERO DOWNLOAD APPROACH
# ══════════════════════════════════════════════════════════════════

async def _process_message(client: TelegramClient, message, notify_chat=None, notify_msg_id=None):
    filename, mime, size, doc = _extract_file_info(message.media)
    if not filename:
        return False

    size_str = _human_size(size)
    clean_caption = _build_clean_caption(filename, size_str)

    log.info("msg_id=%-8d  Processing (Zero-DL): %s (%s)", message.id, filename, size_str)

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

    # ── INSTANT UPLOAD (Passing message.media skips downloading) ──
    uploaded = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client.send_file(
                CHANNEL_ID,
                file=message.media,
                caption=clean_caption,
                parse_mode="md"
            )
            uploaded = True
            log.info("msg_id=%-8d  Uploaded instantly with clean caption.", message.id)
            break
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            log.error("msg_id=%-8d  Upload attempt %d failed: %s", message.id, attempt, e)
            await asyncio.sleep(2 ** attempt)

    if not uploaded:
        if status_msg:
            await status_msg.edit(f"❌ Upload failed for `{filename}`.")
        return False

    # ── DELETE ORIGINAL MESSAGE ───────────────────────────────────
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

    if status_msg:
        try:
            await status_msg.edit(
                f"✅ **Done!**\n"
                f"📄 `{filename}`\n"
                f"🏷️ Caption cleaned & Raj Dev branding added."
            )
        except Exception:
            pass

    log.info("msg_id=%-8d  [COMPLETE] %s", message.id, filename)
    return True

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

    @client.on(events.NewMessage(pattern=r"^/start$"))
    async def cmd_start(event):
        sender = await event.get_sender()
        name   = getattr(sender, "first_name", "there") or "there"
        await event.reply(
            f"👋 **Hello {name}! Welcome.**\n\n"
            f"I am **{_dev_name} Caption Bot (Lightning Fast Edition)**\n"
            f"Telegram: {_dev_tg}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**What I do:**\n"
            f"📌 Remove old captions, links & usernames INSTANTLY\n"
            f"📌 No downloading/uploading overhead\n"
            f"📌 Auto-detect files in channel and fix them\n\n"
            f"Type /help to see all commands.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        log.info("/start from %s (id=%d)", name, sender.id)

    @client.on(events.NewMessage(pattern=r"^/raj$"))
    async def cmd_raj(event):
        await event.reply(
            f"👨‍💻 **Developer Info**\n\n"
            f"🔹 Name    : **{_dev_name}**\n"
            f"🔹 Telegram: **{_dev_tg}**\n"
            f"🔹 Role    : Bot Developer & Owner\n"
            f"🔹 Build   : Auto Caption Cleaner (Zero-DL Edition)\n\n"
            f"⚡ Powered by Telethon + Asyncio\n"
            f"🔒 Integrity-locked. Tamper = crash."
        )

    @client.on(events.NewMessage(pattern=r"^/help$"))
    async def cmd_help(event):
        await event.reply(
            f"📖 **{_dev_name} Caption Bot — Help**\n\n"
            f"**⚙️ Auto Mode:**\n"
            f"Bas apne channel mein koi bhi file post karo.\n"
            f"Bot automatically:\n"
            f"  ✅ Purana link/username hatayega\n"
            f"  ✅ Sirf naam aur size rakhega\n"
            f"  ✅ Original message delete karega\n\n"
            f"**🔐 Bot Permissions required:**\n"
            f"  • Post Messages ✅\n"
            f"  • Delete Messages ✅"
        )

    @client.on(events.NewMessage(pattern=r"^/status$"))
    async def cmd_status(event):
        q_size = _queue.qsize() if _queue else 0
        await event.reply(
            f"📊 **Bot Status**\n\n"
            f"🟢 Status     : **Live & Running (Zero-DL Mode)**\n"
            f"👷 Workers    : {MAX_WORKERS} async\n"
            f"📥 Queue size : {q_size} pending\n"
            f"📡 Channel    : `{CHANNEL_ID}`\n"
            f"👤 Developer  : {_dev_name} ({_dev_tg})"
        )

    @client.on(events.NewMessage(pattern=r"^/clean$", chats=CHANNEL_ID))
    async def cmd_clean(event):
        if not event.message.reply_to_msg_id:
            return
        try:
            target = await client.get_messages(CHANNEL_ID, ids=event.message.reply_to_msg_id)
        except Exception:
            return
        if not target or not target.media:
            return
        
        try:
            await client.delete_messages(CHANNEL_ID, [event.message.id])
        except Exception:
            pass
            
        await _queue.put((target, None, None))

    # ── Auto mode: new file in channel ────────────────────────────
    @client.on(events.NewMessage(chats=CHANNEL_ID))
    async def on_channel_file(event):
        msg = event.message
        
        # Skip if no media or it's a photo
        if not msg.media or isinstance(msg.media, MessageMediaPhoto):
            return
            
        # Infinite loop prevention: agar bot ka branding already hai, toh skip karo
        cap = msg.message or ""
        if f"Uploaded by: **{_dev_name}**" in cap or f"Uploaded by: {_dev_name}" in cap:
            return
            
        filename, _, _, _ = _extract_file_info(msg.media)
        if not filename:
            return
            
        log.info("msg_id=%-8d  Auto-queued: %s", msg.id, filename)
        await _queue.put((msg, None, None))

    log.info("All handlers registered successfully.")

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

    _semaphore = asyncio.Semaphore(MAX_WORKERS)
    _queue     = asyncio.Queue(maxsize=200)

    client = TelegramClient(
        "raj_dev_caption_session",
        API_ID, API_HASH,
        connection_retries=10,
        retry_delay=5,
        flood_sleep_threshold=60,
        device_model="RajDevCaptionBot/2.0",
        system_version="Linux",
        app_version="2.0.0",
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
  
