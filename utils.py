# utils.py
import re
import hashlib
import base64
import sys
import os
from pathlib import Path

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
\033[1;36m ██████╗  █████╗      ██╗    ██████╗ ███████╗██╗   ██╗
 ██╔══██╗██╔══██╗     ██║    ██╔══██╗██╔════╝██║   ██║
 ██████╔╝███████║     ██║    ██║  ██║█████╗  ██║   ██║
 ██╔══██╗██╔══██║██   ██║    ██║  ██║██╔══╝  ╚██╗ ██╔╝
 ██║  ██║██║  ██║╚█████╔╝    ██████╔╝███████╗ ╚████╔╝
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚════╝     ╚═════╝ ╚══════╝  ╚═══╝\033[0m
\033[1;33m  ┌──────────────────────────────────────────────────────┐
  │  Developer  : {dev_name:<37}│
  │  Telegram   : {dev_tg:<37}│
  │  Mode       : Multi-Lang + Custom Thumbnail Mode      │
  └──────────────────────────────────────────────────────┘\033[0m
""")

# ══════════════════════════════════════════════════════════════════
#  SMART CAPTION & LANGUAGE BUILDER
# ══════════════════════════════════════════════════════════════════

def detect_language(filename: str) -> str:
    """Detects language based on filename keywords."""
    lower_name = filename.lower()
    if any(word in lower_name for word in ['bengali', 'bangla', 'beng']):
        return "🌐 **Language:** Bengali (বাংলা)"
    elif any(word in lower_name for word in ['hindi', 'hin']):
        return "🌐 **Language:** Hindi (हिंदी)"
    elif any(word in lower_name for word in ['english', 'eng']):
        return "🌐 **Language:** English"
    else:
        return "🌐 **Language:** Multi/Unknown"

def build_clean_caption(original_filename: str, size_str: str, dev_name: str, dev_tg: str) -> str:
    """Cleans filename and builds multi-language caption."""
    # Remove @usernames and links
    clean_name = re.sub(r'@[a-zA-Z0-9_]+', '', original_filename)
    clean_name = re.sub(r'https?://\S+|t\.me/\S+', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'[_\-]+', ' ', clean_name).strip()
    
    if not clean_name:
        clean_name = original_filename

    lang_tag = detect_language(clean_name)

    return (
        f"🎬 **{clean_name}**\n\n"
        f"📦 **Size:** {size_str}\n"
        f"{lang_tag}\n\n"
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
      
