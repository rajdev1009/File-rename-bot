<div align="center">

<img src="https://i.ibb.co/qFyMDRk8/IMG-20251130-WA0108-2.jpg" width="100%" style="border-radius: 15px; box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.5);" alt="Raj Dev Banner">

# 🌌 RAJ DEV • ULTIMATE FILE RENAMER BOT 🌌
### ⚡ High-Speed | 3D-Architecture | Multi-Tasking Async Engine ⚡

Backend Powered by **Telethon (Asyncio)** • Hardlocked Security by **Raj Dev**

p
[![](https://img.shields.io/badge/Developer-Raj__Dev-00f2fe?style=for-the-badge&logo=telegram&logoColor=white&box-shadow=true)](https://t.me/raj_dev_01)
[![](https://img.shields.io/badge/Telegram-@raj__dev__01-0077ff?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/raj_dev_01)
[![](https://img.shields.io/badge/Deployment-Koyeb%20%2F%20Render-ff007f?style=for-the-badge&logo=docker&logoColor=white)](https://koyeb.com)

---
<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png" width="100%">
</div>

## 🧬 प्रोजेक्ट आर्किटेक्चर और लॉजिक (How It Works)

यह बॉट सामान्य बॉट्स जैसा नहीं है। इसे भारी लोड (25-50 फाइलें एक साथ) संभालने के लिए डिज़ाइन किया गया है:
* **Asynchronous Queue Pipeline:** जब चैनल में एक साथ 25+ फाइलें आती हैं, तो वे क्रैश होने के बजाय `asyncio.Queue` में चली जाती हैं और 25 पैरेलल वर्कर्स उन्हें एक-एक करके प्रोसेस करते हैं।
* **2GB Streaming Support:** बिना रैम क्रैश किए यह बड़ी फाइलों को यूनीक टोकन नाम से डाउनलोड और रीनेम करता है।
* **Anti-Tamper Lock:** कोड के अंदर डेवलपर का नाम `Raj Dev` और यूजरनेम `base64` और `SHA-256` हैश से लॉक है। नाम बदलने पर बॉट खुद को नष्ट (`os._exit(1)`) कर लेगा।

---

## 🚀 3D क्लाउड डिप्लॉयमेंट गाइड (Koyeb / Render)

Koyeb या Render डैशबोर्ड पर इस पावरफुल इंजन को लाइव करने के लिए नीचे दिए गए 3D-स्टाइल स्टेप्स को फॉलो करें:

### 📥 STEP 1: गिटहब पर पुश (Push to GitHub)
अपनी रिपॉजिटरी में इन तीनों फाइलों को अपलोड करें:
1. `raj_dev_renamer_bot.py` (मेन इंजन कोड)
2. `requirements.txt` (डिपेंडेंसी)
3. `Dockerfile` (एनवायरनमेंट सेटअप)

### ⚙️ STEP 2: एनवायरनमेंट वेरिएबल्स सेट करें (Environment Variables)
Koyeb डैशबोर्ड में **New App** बनाएं, अपना GitHub सिलेक्ट करें और **Environment Variables** टैब में ये चाबियां भरें:

| 🔑 VARIABLE KEY | 📝 DESCRIPTION | 💡 EXAMPLE VALUE |
| :--- | :--- | :--- |
| **`API_ID`** | टेलीग्राम से मिला API ID | `1234567` |
| **`API_HASH`** | टेलीग्राम से मिला API Hash | `b38e...9ac2` |
| **`BOT_TOKEN`** | BotFather का सीक्रेट टोकन | `71234:AAH_x...` |
| **`CHANNEL_ID`** | टारगेट चैनल आईडी (`-100` के साथ) | `-1001234567890` |

### 💾 STEP 3: परसिस्टेंट वॉल्यूम माउंट (Persistent Volume)
> ⚠️ **महत्वपूर्ण:** यदि आप वॉल्यूम माउंट नहीं करेंगे, तो हर रीस्टार्ट पर टेलीग्राम लॉगिन सेशन डिलीट हो जाएगा।

Koyeb में **Volumes** सेक्शन में जाएं और निम्नलिखित दो पाथ माउंट करें:
* 📁 `/app/tmp_raj_dev` — *अस्थायी फाइलों (Temp Files) के प्रोसेसिंग के लिए।*
* 🔑 `/app/session` — *Telethon Session डेटा सुरक्षित रखने के लिए (Zaroori Hai!).*

---

<div align="center">

## 🖥️ डिप्लॉयमेंट कंसोल लाइव स्टेटस (Terminal View)

जब आपका बॉट सफलतापूर्वक क्लाउड पर डिप्लॉय हो जाएगा, तो आपके कंसोल/लॉग्स में यह शानदार शानदार 3D-स्टाइल नियॉन बैनर और तुम्हारी वॉइस लाइन चमकेगी:

```cyan
 ██████╗  █████╗      ██╗    ██████╗ ███████╗██╗   ██╗
 ██╔══██╗██╔══██╗     ██║    ██╔══██╗██╔════╝██║   ██║
 ██████╔╝███████║     ██║    ██║  ██║█████╗  ██║   ██║
 ██╔══██╗██╔══██║██   ██║    ██║  ██║██╔══╝  ╚██╗ ██╔╝
 ██║  ██║██║  ██║╚█████╔╝    ██████╔╝███████╗ ╚████╔╝
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚════╝     ╚═════╝ ╚══════╝  ╚═══╝

 ┌─────────────────────────────────────────────────────┐
 │  Developer  :  Raj Dev                              │
 │  Telegram   :  @raj_dev_01                          │
 │  Status     :  Authorized ✅                         │
 └─────────────────────────────────────────────────────┘

 >> Hello, I am Raj. I am now live! 🚀
