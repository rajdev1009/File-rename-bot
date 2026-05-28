# bot.py
import os
import sys
import asyncio
import logging
import time
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaPhoto

# utils.py se aapka strict integrity aur functions import
from utils import (
    run_integrity_check, print_banner, build_clean_caption, 
    extract_file_info, human_size
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("RajDevBot")

API_ID      = int(os.environ.get("API_ID", "0"))
API_HASH    = os.environ.get("API_HASH", "").strip()
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID  = int(os.environ.get("CHANNEL_ID", "0"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "10"))
TEMP_DIR    = "./tmp_raj_dev"

# Credit Lock Check
dev_name, dev_tg = run_integrity_check()

_semaphore = asyncio.Semaphore(MAX_WORKERS)
_queue     = asyncio.Queue(maxsize=200)
client     = TelegramClient("session_rajdev", API_ID, API_HASH)

# ══════════════════════════════════════════════════════════════════
#  HEALTH SERVER (KOYEB FIX - BOT KABHI STOP NAHI HOGA)
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
    log.info(f"Health server running on port {port}")
    async with srv:
        await srv.serve_forever()

# ══════════════════════════════════════════════════════════════════
#  LIVE PROGRESS BAR LOGIC (SPEED, ETA, SIZE)
# ══════════════════════════════════════════════════════════════════

def get_progress_callback(status_msg, action_text):
    start_time = time.time()
    last_update_time = [0]
    
    async def cb(current, total):
        now = time.time()
        # Har 3 second mein update taaki Telegram block na kare
        if now - last_update_time[0] > 3 or current == total:
            last_update_time[0] = now
            if total == 0: return
            
            percentage = current * 100 / total
            bar_length = 15
            filled = int(bar_length * (current / total))
            bar = '█' * filled + '░' * (bar_length - filled)
            
            elapsed = now - start_time
            speed = current / elapsed if elapsed > 0 else 0
            eta = (total - current) / speed if speed > 0 else 0
            
            text = (
                f"⏳ **{action_text}**\n\n"
                f"[{bar}] **{percentage:.1f}%**\n"
                f"📦 Size: {human_size(current)} / {human_size(total)}\n"
                f"⚡ Speed: {human_size(speed)}/s\n"
                f"⏱ ETA: {int(eta)}s"
            )
            try:
                await status_msg.edit(text)
            except Exception:
                pass 
    return cb

# ══════════════════════════════════════════════════════════════════
#  CORE PROCESSOR (Zero-Download Default)
# ══════════════════════════════════════════════════════════════════

async def _process_message(message):
    filename, mime, size, doc = extract_file_info(message.media)
    if not filename: return False

    size_str = human_size(size)
    clean_caption = build_clean_caption(filename, size_str, dev_name, dev_tg)

    try:
        # Zero Download Fast Upload
        await client.send_file(CHANNEL_ID, file=message.media, caption=clean_caption, parse_mode="md")
        log.info(f"msg_id={message.id} | Auto-Clean Success | {filename}")
        
        # Delete Original Message
        await client.delete_messages(CHANNEL_ID, [message.id])
    except Exception as e:
        log.error(f"Error processing {filename}: {e}")

async def _worker():
    while True:
        message = await _queue.get()
        if message is None: break
        async with _semaphore:
            await _process_message(message)
        _queue.task_done()

# ══════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/start$"))
async def start(event):
    await event.reply(
        f"👋 **Welcome to {dev_name} Multi-Lang Bot!**\n\n"
        f"Commands available:\n"
        f"▶️ /help - How to use\n"
        f"▶️ /thumb - Add custom thumbnail\n"
        f"▶️ /status - Check bot queue\n"
        f"▶️ /raj - Developer info"
    )

@client.on(events.NewMessage(pattern=r"^/help$"))
async def help_cmd(event):
    await event.reply(
        "🛠 **Commands:**\n\n"
        "1. **Auto Mode:** Channel me file daalo, instant caption clean hoga.\n"
        "2. **/thumb:** Naya thumbnail lagane ke liye. Kisi video pe apni nayi photo aur caption `/thumb` ke sath reply karo.\n"
        "3. **/clean:** Kisi message pe reply karke usko manually clean karne ke liye."
    )

@client.on(events.NewMessage(pattern=r"^/raj$"))
async def cmd_raj(event):
    await event.reply(
        f"👨‍💻 **Developer Info**\n\n"
        f"🔹 Name    : **{dev_name}**\n"
        f"🔹 Telegram: **{dev_tg}**\n"
        f"🔹 Role    : Bot Developer & Owner\n"
        f"🔹 Build   : AstraToonix Edition (Multi-Lang + Thumb)\n\n"
        f"🔒 Integrity-locked Code."
    )

@client.on(events.NewMessage(pattern=r"^/status$"))
async def cmd_status(event):
    q_size = _queue.qsize() if _queue else 0
    await event.reply(
        f"📊 **Bot Status**\n\n"
        f"🟢 Status     : **Live & Running**\n"
        f"👷 Workers    : {MAX_WORKERS} async\n"
        f"📥 Queue size : {q_size} pending files\n"
        f"👤 Developer  : {dev_name}"
    )

@client.on(events.NewMessage(pattern=r"^/clean$"))
async def cmd_clean(event):
    if not event.message.reply_to_msg_id:
        return await event.reply("⚠️ Kisi file ko **reply** karke /clean likho.")
    try:
        target = await client.get_messages(event.chat_id, ids=event.message.reply_to_msg_id)
        if not target or not target.media:
            return await event.reply("⚠️ Replied message mein koi file nahi hai.")
        
        # Add to queue manually
        await _queue.put(target)
        await event.reply("✅ Added to manual processing queue.")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

# ── NAYA FEATURE: CUSTOM THUMBNAIL WITH LIVE PROGRESS ──
@client.on(events.NewMessage(pattern=r"^/thumb$"))
async def set_thumb(event):
    if not event.is_reply:
        return await event.reply("⚠️ Kisi document/video ko reply karke apna photo aur `/thumb` likh ke bhejo.")
    
    if not event.media or not isinstance(event.media, MessageMediaPhoto):
        return await event.reply("⚠️ Tumne command bheja par photo attach nahi ki! Ek photo attach karke target file ko reply karo.")

    target_msg = await event.get_reply_message()
    filename, _, size, _ = extract_file_info(target_msg.media)
    
    if not filename:
        return await event.reply("⚠️ Jisko reply kiya hai usme koi file nahi hai.")

    size_str = human_size(size)
    clean_caption = build_clean_caption(filename, size_str, dev_name, dev_tg)
    
    os.makedirs(TEMP_DIR, exist_ok=True)
    status = await event.reply("⏳ Thumbnail process initializing...")

    try:
        await status.edit("📥 Downloading Thumbnail Photo...")
        thumb_path = await event.download_media(file=TEMP_DIR)

        cb_download = get_progress_callback(status, "Downloading Original File...")
        video_path = await target_msg.download_media(file=TEMP_DIR, progress_callback=cb_download)

        cb_upload = get_progress_callback(status, "Uploading with New Thumbnail...")
        await client.send_file(
            event.chat_id, 
            video_path, 
            thumb=thumb_path, 
            caption=clean_caption, 
            force_document=False,
            progress_callback=cb_upload
        )
        
        await status.edit("✅ **Thumbnail successfully updated!**")
        
        await asyncio.sleep(2) 
        await client.delete_messages(event.chat_id, [target_msg.id, event.id, status.id])
        os.remove(thumb_path)
        os.remove(video_path)
        
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

# ── AUTO MODE: DIRECT CHANNEL TRIGGER ──
@client.on(events.NewMessage(chats=CHANNEL_ID))
async def on_channel_file(event):
    msg = event.message
    if not msg.media or isinstance(msg.media, MessageMediaPhoto): return
    
    cap = msg.message or ""
    if f"Uploaded by: **{dev_name}**" in cap: return 
    
    await _queue.put(msg)

# ══════════════════════════════════════════════════════════════════
#  START
# ══════════════════════════════════════════════════════════════════

async def main():
    print_banner(dev_name, dev_tg)
    if not API_ID or not BOT_TOKEN:
        sys.exit("\n[FATAL] Missing Environment Variables.\n")
    
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    log.info(f"Bot Active: @{me.username}")
    
    workers = [asyncio.create_task(_worker()) for _ in range(MAX_WORKERS)]
    
    # Ye block Koyeb ka Port 8000 server aur Telegram client dono ek sath chalayega
    await asyncio.gather(
        _health_server(),
        client.run_until_disconnected(),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
        
