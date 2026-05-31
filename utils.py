# utils.py
import re
import hashlib
import base64
import sys
import os
import asyncio
import urllib.parse
import aiohttp
from pathlib import Path
from huggingface_hub import AsyncInferenceClient

# ══════════════════════════════════════════════════════════════════
#  INTEGRITY ENGINE & BANNER
# ══════════════════════════════════════════════════════════════════

_DEV_NAME_B64    = b"UmFqIERldg=="
_DEV_TG_B64      = b"QHJhal9kZXZfMDE="
_DEV_NAME_SHA256 = "b036a790a298cf1e384234a29346ef00760880bea09c09d1f82f1c36d841db22"
_DEV_TG_SHA256   = "92860b13c4576cc10d5903abdda63ec8b46d0aec050ab05dceed4299893fb9a6"

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def run_integrity_check() -> tuple:
    try:
        dev_name = base64.b64decode(_DEV_NAME_B64).decode()
        dev_tg   = base64.b64decode(_DEV_TG_B64).decode()
    except Exception:
        sys.exit("\n[FATAL] Identity decode failed.\n")
    if _sha256(dev_name) != _DEV_NAME_SHA256 or _sha256(dev_tg) != _DEV_TG_SHA256:
        sys.exit("\n[FATAL] Checksum mismatch.\n")
    return dev_name, dev_tg

def print_banner(dev_name: str, dev_tg: str):
    print(f"""
\033[1;36m ██████╗  █████╗          ██╗    ██████╗ ███████╗ ██╗    ██╗
           ██╔══██╗██╔══██╗       ██║    ██╔══██╗██╔════╝██║    ██║
           ██████╔╝███████║       ██║    ██║   ██║█████╗    ██║   ██║
           ██╔══██╗██╔══██║ ██   ██║    ██║   ██║██╔══╝  ╚██╗ ██╔╝
           ██║   ██║██║    ██╚█████╔╝    ██████╔╝███████╗╚████╔╝
           ╚═╝  ╚═╝╚═╝    ╚═╝ ╚════╝     ╚═════╝ ╚══════╝  ╚═══╝\033[0m
\033[1;33m  ┌──────────────────────────────────────────────────────┐
  │  Developer  : {dev_name:<37}│
  │  Telegram   : {dev_tg:<37}│
  │  Mode       : AstraToonix AI Edition (Qwen 2.5 + Hybrid)│
  └──────────────────────────────────────────────────────┘\033[0m
""")

# ══════════════════════════════════════════════════════════════════
#  HYBRID AI INTEGRATION
# ══════════════════════════════════════════════════════════════════

HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
hf_client = AsyncInferenceClient(token=HF_TOKEN) if HF_TOKEN else None

# Best Open Source Model for Text/Chat
TEXT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# TEXT (Captions) Model 
async def get_ai_caption_text(filename: str) -> str:
    if not hf_client:
        return ""
    
    messages = [
        {"role": "system", "content": "You are a witty comedy writer. Write a single-line funny, engaging caption for the given video title. Reply in Hinglish (Hindi + English). Do not use quotes or hashtags."},
        {"role": "user", "content": f"Video title: {filename}"}
    ]
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = await hf_client.chat_completion(
                messages,
                model=TEXT_MODEL,
                max_tokens=60
            )
            clean_res = res.choices[0].message.content.replace('"', '').strip()
            return f"🤖 **AI Vibe:** {clean_res}\n"
        except Exception as e:
            error_msg = str(e).lower()
            print(f"Caption API Error (Attempt {attempt+1}): {error_msg}")
            if "503" in error_msg or "loading" in error_msg or "timeout" in error_msg:
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
            else:
                break
    return ""

# TEXT (Chat) Model
async def chat_with_ai(user_message: str) -> str:
    if not hf_client:
        return "Bhai, mera AI engine abhi offline hai. HF_TOKEN set nahi hai."
    
    system_prompt = (
        "You are the official AI assistant of the AstraToonix YouTube channel. "
        "You were created ONLY and strictly by Raj Dev. Never mention Google, OpenAI, or any other company as your creator. "
        "Your creator, Raj Dev, was born on July 21, 2002. He lives in Lumding, Assam, India. "
        "Raj Dev is a highly skilled full-stack developer (MERN stack, Python), a Railway S&T Supervisor, and the creator of AstraToonix. "
        "Always reply in a friendly, conversational Hinglish (Hindi + English) tone. Keep answers concise."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = await hf_client.chat_completion(
                messages, 
                model=TEXT_MODEL, 
                max_tokens=150,
                temperature=0.7
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e).lower()
            print(f"Chat API Error (Attempt {attempt+1}): {error_msg}")
            if "503" in error_msg or "loading" in error_msg or "timeout" in error_msg:
                if attempt < max_retries - 1:
                    print("⏳ Text Model overloaded. Waiting 3 seconds before retry...")
                    await asyncio.sleep(3)
            else:
                break
                
    return "Yaar abhi HF ke servers par load hai, main connect nahi kar paa raha. Thodi der me text karna!"

# IMAGE Generation Model - Hybrid (HF + Pollinations Fallback)
async def generate_ai_thumbnail_image(prompt: str, save_path: str) -> bool:
    # ── STEP 1: Hugging Face with Retry Logic ──
    if hf_client:
        image_model = "black-forest-labs/FLUX.1-schnell" 
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"Trying HF ({image_model}) - Attempt {attempt + 1}...")
                image = await hf_client.text_to_image(prompt, model=image_model)
                image.save(save_path)
                return True
            except Exception as e:
                error_msg = str(e).lower()
                if "503" in error_msg or "loading" in error_msg or "timeout" in error_msg:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(8)
                else:
                    break 

    # ── STEP 2: 100% Guarantee Fallback (Pollinations AI) ──
    print("⚠️ HF failed. Switching to Pollinations AI Fallback...")
    try:
        safe_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as f:
                        f.write(await response.read())
                    return True
                else:
                    return False
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════════
#  SMART CAPTION & LANGUAGE BUILDER
# ══════════════════════════════════════════════════════════════════

def detect_language(filename: str) -> str:
    lower_name = filename.lower()
    if any(word in lower_name for word in ['bengali', 'bangla', 'beng']):
        return "🌐 **Language:** Bengali (বাংলা)"
    elif any(word in lower_name for word in ['hindi', 'hin']):
        return "🌐 **Language:** Hindi (हिंदी)"
    elif any(word in lower_name for word in ['english', 'eng']):
        return "🌐 **Language:** English"
    else:
        return "🌐 **Language:** Multi/Unknown"

async def build_clean_caption(original_filename: str, size_str: str, dev_name: str, dev_tg: str) -> str:
    clean_name = re.sub(r'@[a-zA-Z0-9_]+', '', original_filename)
    clean_name = re.sub(r'https?://\S+|t\.me/\S+', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'[_\-]+', ' ', clean_name).strip()
    
    if not clean_name:
        clean_name = original_filename

    lang_tag = detect_language(clean_name)
    ai_addon = await get_ai_caption_text(clean_name)

    return (
        f"🎬 **{clean_name}**\n\n"
        f"📦 **Size:** {size_str}\n"
        f"{lang_tag}\n"
        f"{ai_addon}\n"
        f"📤 Uploaded by: **{dev_name}**\n"
        f"📢 Channel: {dev_tg}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

def extract_file_info(media) -> tuple:
    if not (media and hasattr(media, "document") and media.document):
        return None, None, 0, None

    doc = media.document
    mime = getattr(doc, "mime_type", "application/octet-stream")
    size = getattr(doc, "size", 0)
    filename = None

    for attr in doc.attributes:
        if hasattr(attr, "file_name") and attr.file_name:
            filename = attr.file_name
            break

    if not filename:
        ext = mime.split("/")[-1] if "/" in mime else "bin"
        filename = f"file.{ext}"

    return filename, mime, size, doc

def human_size(size_bytes: int) -> str:
    if size_bytes < 1024: return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2: return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 ** 3: return f"{size_bytes/1024**2:.1f} MB"
    else: return f"{size_bytes/1024**3:.2f} GB"
    
