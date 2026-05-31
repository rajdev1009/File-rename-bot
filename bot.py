# bot.py
import os
import sys
import asyncio
import logging
import time
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaPhoto, DocumentAttributeVideo, DocumentAttributeFilename

# utils.py se functions import
from utils import (
    run_integrity_check, print_banner, build_clean_caption, 
    extract_file_info, human_size, generate_ai_thumbnail_image, HF_TOKEN,
    chat_with_ai
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("RajDevBot")

API_ID      = int(os.environ.get("API_ID", "0"))
API_HASH    = os.environ.get("API_HASH", "").strip()
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID  = int(os.environ.get("CHANNEL_ID", "0"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "10"))
TEMP_DIR    = "./tmp_raj_dev"

dev_name, dev_tg = run_integrity_check()

_semaphore = asyncio.Semaphore(MAX_WORKERS)
_queue     = asyncio.Queue(maxsize=200)
client     = TelegramClient("session_rajdev", API_ID, API_HASH)

# ══════════════════════════════════════════════════════════════════
#  HEALTH SERVER 
# ══════════════════════════════════════════════════════════════════

async def _health_server():
    port = int(os.environ.get("PORT", "7860"))
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
#  LIVE PROGRESS BAR LOGIC
# ══════════════════════════════════════════════════════════════════

def get_progress_callback(status_msg, action_text):
    start_time = time.time()
    last_update_time = [0]
    
    async def cb(current, total):
        now = time.time()
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

def _is_video(filename, mime):
    if mime and 'video' in mime.lower():
        return True
    if filename and filename.lower().endswith(('.mp4', '.mkv', '.avi', '.webm')):
        return True
    return False

def _build_video_attributes(filename, is_video):
    attrs = [DocumentAttributeFilename(file_name=filename)]
    if is_video:
        attrs.append(DocumentAttributeVideo(
            duration=1, 
            w=1280, 
            h=720, 
            supports_streaming=True
        ))
    return attrs

# ══════════════════════════════════════════════════════════════════
#  CORE PROCESSOR (Auto Clean with AI Caption)
# ══════════════════════════════════════════════════════════════════

async def _process_message(message):
    filename, mime, size, doc = extract_file_info(message.media)
    if not filename: return False

    size_str = human_size(size)
    clean_caption = await build_clean_caption(filename, size_str, dev_name, dev_tg)
    video_flag = _is_video(filename, mime)
    media_attrs = _build_video_attributes(filename, video_flag)

    try:
        await client.send_file(
            CHANNEL_ID, 
            file=message.media, 
            caption=clean_caption, 
            parse_mode="md",
            attributes=media_attrs,
            force_document=not video_flag,
            supports_streaming=video_flag
        )
        log.info(f"msg_id={message.id} | AI Auto-Clean Success | {filename}")
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
        f"👋 **Welcome to {dev_name} AI Edition Bot!**\n\n"
        f"Commands available:\n"
        f"▶️ /help - How to use\n"
        f"▶️ /thumb - Add manual custom thumbnail\n"
        f"▶️ /aithumb [prompt] - Generate & add AI thumbnail\n"
        f"▶️ /status - Check bot queue\n"
        f"▶️ /clean - Manual file clean\n"
        f"▶️ /raj - Developer info\n\n"
        f"💡 Tip: Aap mujhse direct normal chat (hi, hello, etc.) bhi kar sakte hain!"
    )

@client.on(events.NewMessage(pattern=r"^/help$"))
async def help_cmd(event):
    await event.reply(
        "🛠 **Commands:**\n\n"
        "1. **Auto Mode:** Channel me file daalo, instant caption clean & AI text generate hoga.\n"
        "2. **/thumb:** Naya manual thumbnail lagane ke liye (photo attach karke reply).\n"
        "3. **/aithumb [text]:** Kisi video ko reply karo aur text likho (e.g., `/aithumb funny cat`), AI khud thumbnail banakar lagayega.\n"
        "4. **/clean:** Kisi message pe reply karke usko manually clean karne ke liye."
    )

@client.on(events.NewMessage(pattern=r"^/raj$"))
async def cmd_raj(event):
    await event.reply(
        f"👨‍💻 **Developer Info**\n\n"
        f"🔹 Name    : **{dev_name}**\n"
        f"🔹 Telegram: **{dev_tg}**\n"
        f"🔹 Build   : AstraToonix AI Edition\n\n"
        f"🔒 Integrity-locked Code."
    )

@client.on(events.NewMessage(pattern=r"^/status$"))
async def cmd_status(event):
    q_size = _queue.qsize() if _queue else 0
    ai_status = "Active ✅" if HF_TOKEN else "Disabled ❌ (Add HF_TOKEN env var)"
    await event.reply(
        f"📊 **Bot Status**\n\n"
        f"🟢 Status     : **Live & Running**\n"
        f"🤖 AI Engine  : {ai_status}\n"
        f"👷 Workers    : {MAX_WORKERS} async\n"
        f"📥 Queue size : {q_size} pending files"
    )

@client.on(events.NewMessage(pattern=r"^/clean$"))
async def cmd_clean(event):
    if not event.message.reply_to_msg_id:
        return await event.reply("⚠️ Kisi file ko **reply** karke /clean likho.")
    try:
        target = await client.get_messages(event.chat_id, ids=event.message.reply_to_msg_id)
        if not target or not target.media:
            return await event.reply("⚠️ Replied message mein koi file nahi hai.")
        
        await _queue.put(target)
        await event.reply("✅ Added to manual processing queue.")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

# ── INLINE SEARCH FEATURE ──
@client.on(events.InlineQuery)
async def inline_search(event):
    query = event.text.lower()
    builder = event.builder
    results = []
    if not query: return
    async for message in client.iter_messages(CHANNEL_ID, search=query, limit=10):
        if message.media:
            title = message.file.name if message.file and message.file.name else (message.message[:50] if message.message else "Media File")
            results.append(builder.document(message.media, title=title, text=f"File: {title}"))
    await event.answer(results)

# ── ORIGINAL FEATURE: MANUAL CUSTOM THUMBNAIL ──
@client.on(events.NewMessage(pattern=r"^/thumb$"))
async def set_thumb(event):
    if not event.is_reply:
        return await event.reply("⚠️ Kisi document/video ko reply karke apna photo aur `/thumb` likh ke bhejo.")
    
    if not event.media or not isinstance(event.media, MessageMediaPhoto):
        return await event.reply("⚠️ Tumne command bheja par photo attach nahi ki!")

    target_msg = await event.get_reply_message()
    filename, mime, size, _ = extract_file_info(target_msg.media)
    
    if not filename:
        return await event.reply("⚠️ Jisko reply kiya hai usme koi file nahi hai.")

    size_str = human_size(size)
    clean_caption = await build_clean_caption(filename, size_str, dev_name, dev_tg)
    
    video_flag = _is_video(filename, mime)
    media_attrs = _build_video_attributes(filename, video_flag)
    
    os.makedirs(TEMP_DIR, exist_ok=True)
    status = await event.reply("⏳ Thumbnail process initializing...")

    thumb_path = None
    video_path = None
    upload_path = None

    try:
        await status.edit("📥 Downloading Thumbnail Photo...")
        thumb_path = await event.download_media(file=TEMP_DIR)

        cb_download = get_progress_callback(status, "Downloading Original File...")
        video_path = await target_msg.download_media(file=TEMP_DIR, progress_callback=cb_download)

        upload_path = video_path
        if video_flag and not video_path.lower().endswith('.mp4'):
            upload_path = video_path + ".mp4"
            os.rename(video_path, upload_path)

        cb_upload = get_progress_callback(status, "Uploading with New Thumbnail...")
        await client.send_file(
            event.chat_id, 
            upload_path,                          
            thumb=thumb_path, 
            caption=clean_caption, 
            parse_mode="md",
            attributes=media_attrs,               
            force_document=not video_flag,        
            supports_streaming=video_flag,        
            progress_callback=cb_upload
        )
        
        await status.edit("✅ **Thumbnail successfully updated!**")
        await asyncio.sleep(2) 
        await client.delete_messages(event.chat_id, [target_msg.id, event.id, status.id])
        
    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        
    finally:
        for path in [thumb_path, video_path, upload_path]:
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass

# ── NEW FEATURE: AI CUSTOM THUMBNAIL GENERATOR ──
@client.on(events.NewMessage(pattern=r"^/aithumb (.+)"))
async def set_ai_thumb(event):
    if not event.is_reply:
        return await event.reply("⚠️ Kisi video ko reply karke `/aithumb <prompt>` likho (e.g., `/aithumb funny cat`).")

    target_msg = await event.get_reply_message()
    filename, mime, size, _ = extract_file_info(target_msg.media)
    
    if not filename:
        return await event.reply("⚠️ Jisko reply kiya hai usme koi file nahi hai.")

    size_str = human_size(size)
    clean_caption = await build_clean_caption(filename, size_str, dev_name, dev_tg)
    
    video_flag = _is_video(filename, mime)
    media_attrs = _build_video_attributes(filename, video_flag)
    
    os.makedirs(TEMP_DIR, exist_ok=True)
    status = await event.reply("⏳ AI Magic Start: Thumbnail generate ho raha hai...")

    prompt = event.pattern_match.group(1).strip()
    thumb_path = os.path.join(TEMP_DIR, f"ai_thumb_{event.id}.jpg")
    video_path = None
    upload_path = None

    try:
        success = await generate_ai_thumbnail_image(prompt, thumb_path)
        if not success:
            return await status.edit("❌ AI API overload ya error! Please try again later.")
            
        cb_download = get_progress_callback(status, "Downloading Original File...")
        video_path = await target_msg.download_media(file=TEMP_DIR, progress_callback=cb_download)

        upload_path = video_path
        if video_flag and not video_path.lower().endswith('.mp4'):
            upload_path = video_path + ".mp4"
            os.rename(video_path, upload_path)

        cb_upload = get_progress_callback(status, "Uploading with AI Thumbnail...")
        await client.send_file(
            event.chat_id, 
            upload_path,                          
            thumb=thumb_path, 
            caption=clean_caption, 
            parse_mode="md",
            attributes=media_attrs,               
            force_document=not video_flag,        
            supports_streaming=video_flag,        
            progress_callback=cb_upload
        )
        
        await status.edit("✅ **AI Thumbnail successfully generated & updated!**")
        await asyncio.sleep(2) 
        await client.delete_messages(event.chat_id, [target_msg.id, event.id, status.id])
        
    except Exception as e:
        await status.edit(f"❌ Error: {e}")
        
    finally:
        for path in [thumb_path, video_path, upload_path]:
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass

# ── NEW FEATURE: CONVERSATIONAL AI CHAT ──
@client.on(events.NewMessage(pattern=r"^(?!/)(.*)", func=lambda e: e.is_private))
async def normal_chat_handler(event):
    if event.media:
        return
        
    user_msg = event.pattern_match.group(1).strip()
    if not user_msg:
        return
        
    async with client.action(event.chat_id, 'typing'):
        ai_reply = await chat_with_ai(user_msg)
        await event.reply(ai_reply)

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
        sys.exit("\n[FATAL] Missing Telegram Environment Variables.\n")
    if not HF_TOKEN:
        log.warning("HF_TOKEN is missing! AI Captions and /aithumb will be disabled.")
    
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    log.info(f"Bot Active: @{me.username}")
    
    workers = [asyncio.create_task(_worker()) for _ in range(MAX_WORKERS)]
    
    await asyncio.gather(
        _health_server(),
        client.run_until_disconnected(),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
        
