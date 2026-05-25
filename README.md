# 🌌 Raj Dev - Channel File Renamer Bot

Telegram channel me ek sath aane wali bhot saari files (videos, documents, audio) ko auto-rename karne ke liye ek advanced aur fast bot. ✨

<div align="center">
  <table style="border: none; border-collapse: collapse; margin: 20px auto;">
    <tr>
      <td style="background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); padding: 6px; border-radius: 20px; box-shadow: 0px 20px 50px rgba(0, 242, 254, 0.45);">
        <img src="https://i.ibb.co/qFyMDRk8/IMG-20251130-WA0108-2.jpg" width="750" style="border-radius: 15px; display: block;" alt="Raj Dev Banner">
      </td>
    </tr>
  </table>

  <br>

  <a href="https://t.me/raj_dev_01">
    <img src="https://img.shields.io/badge/Telegram-Profile-0088cc?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Profile">
  </a>
  &nbsp;
  <a href="https://instagram.com/itz_dminem_official43">
    <img src="https://img.shields.io/badge/Instagram-Profile-e1306c?style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram Profile">
  </a>
  &nbsp;
  <a href="https://t.me/raj_dev_01">
    <img src="https://img.shields.io/badge/Telegram-Channel-0088cc?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Channel">
  </a>
</div>

---

## 🛠️ Bot Features & Logic Box 📦

<table width="100%">
  <tr>
    <td style="background: rgba(255,255,255,0.05); border: 1px solid #00f2fe; border-radius: 10px; padding: 15px;">
      <h3>📥 1. Auto-Fetch & Detect</h3>
      <p>Jab bhi aap apne channel me koi file upload ya forward karoge, bot use turant bina kisi delay ke detect kar lega. ⚡</p>
    </td>
  </tr>
  <tr>
    <td style="background: rgba(255,255,255,0.05); border: 1px solid #4facfe; border-radius: 10px; padding: 15px;">
      <h3>✏️ 2. Auto-Rename Format</h3>
      <p>Bot file ka original name scan karega aur uske aage aapka naam fix kar dega: <b>`Raj Dev - [Original_Name].[ext]`</b>. 🏷️</p>
    </td>
  </tr>
  <tr>
    <td style="background: rgba(255,255,255,0.05); border: 1px solid #00f2fe; border-radius: 10px; padding: 15px;">
      <h3>🚀 3. Parallel Worker Queue</h3>
      <p>Agar aap ek sath 25-30 heavy files bhi forward karoge, toh bot queue bana kar 25 parallel workers ke sath sabko ek sath process karega. Bot bilkul hang nahi hoga! ⛓️</p>
    </td>
  </tr>
  <tr>
    <td style="background: rgba(255,255,255,0.05); border: 1px solid #4facfe; border-radius: 10px; padding: 15px;">
      <h3>🧹 4. Auto-Clean Storage</h3>
      <p>File rename hoke wapas channel me upload hote hi, bot purani file ko channel se automatic delete kar dega taaki double post na ho, aur server storage bhi clean rakhega. 🗑️</p>
    </td>
  </tr>
  <tr>
    <td style="background: rgba(255,255,255,0.05); border: 1px solid #ff007f; border-radius: 10px; padding: 15px;">
      <h3>🛡️ 5. Hardlocked Integrity Check</h3>
      <p>Developer ka credit block Base64 aur SHA-256 se deeply locked hai. Agar koi code se Raj Dev ka naam hatane ki koshish karega toh bot instantly self-crash ho jayega. 🔐</p>
    </td>
  </tr>
</table>

---

## 🌐 How It Works / সিস্টেম লজিক / काम करने का तरीका 🧬

> 👇 **Neeche diye gaye boxes par click karke apni bhasha (Language) me complete logic check karein:**

<details>
<summary><b>🇮🇳 1. HINDI LOGIC BOX (क्लिक करें)</b></summary>
<br>
<table width="100%">
  <tr>
    <td style="background: #1e293b; border: 2px solid #ff9900; border-radius: 12px; padding: 15px; color: #f8fafc;">
      <h4>🛠️ कतार और वर्कर मैनेजमेंट:</h4>
      <p>यह रोबोट बैकग्राउंड में एक शक्तिशाली <b>एसिंक कतार (Async Queue)</b> पर काम करता है। जब आपके टेलीग्राम चैनल में एक साथ ढेर सारी भारी मूवी या फाइल्स आती हैं, तो वे अटके बिना कतार में चली जाती हैं। बैकग्राउंड में लगे २५ वर्कर्स उन्हें पैरेलल डाउनलोड और अपलोड करते हैं, जिससे आपका क्लाउड सर्वर क्रैश नहीं होता। काम पूरा होते ही पुरानी फाइल डिलीट हो जाती है और नई फाइल आपके नाम से सज जाती है! 😎</p>
    </td>
  </tr>
</table>
</details>

<br>

<details>
<summary><b>🇧🇩 2. BENGALI LOGIC BOX (ক্লিক করুন)</b></summary>
<br>
<table width="100%">
  <tr>
    <td style="background: #1e293b; border: 2px solid #22c55e; border-radius: 12px; padding: 15px; color: #f8fafc;">
      <h4>⚙️ সিস্টেম মেকানিজম এবং আর্কিটেকচার:</h4>
      <p>এই বটটি একটি অ্যাডভান্সড <b>অ্যাসিনক্রোনাস কিউ (Async Queue)</b> আর্কিটেকচার ব্যবহার করে তৈরি করা হয়েছে। চ্যানেলে একসাথে ২৫ থেকে ৫০টি ফাইল আপলোড বা ফরোয়ার্ড করা হলে, বটটি কোনো হ্যাং বা ক্র্যাশ ছাড়াই ব্যাকগ্রাউন্ডে ২৫টি প্যারালাল ওয়ার্কারের মাধ্যমে প্রতিটা ফাইল রিনেম করে। আপলোড শেষ হওয়া মাত্রই লোকাল মেমোরি ক্লিয়ার করতে আগের ফাইলটি স্বয়ংক্রিয়ভাবে চ্যানেল থেকে মুছে যায়। 🚀</p>
    </td>
  </tr>
</table>
</details>

<br>

<details>
<summary><b>🇬🇧 3. ENGLISH LOGIC BOX (Click Here)</b></summary>
<br>
<table width="100%">
  <tr>
    <td style="background: #1e293b; border: 2px solid #0077ff; border-radius: 12px; padding: 15px; color: #f8fafc;">
      <h4>🧬 Concurrency Pipeline & Scaling:</h4>
      <p>The core engine initializes an isolated asynchronous queue pipeline running up to 25 parallel tasks. When sudden bulk traffic (up to 2GB per file) hits the channel, the messages are held safely inside the buffer memory. Workers pull elements concurrently, eliminating memory exhaustion leaks on platforms like Koyeb or Render, ensuring premium stability.</p>
    </td>
  </tr>
</table>
</details>

---

## 🚀 Koyeb / Render Deployment Steps

Is bot ko cloud par 24/7 live rakhne ke liye ye simple steps follow karein:

### 1. GitHub me Files Push Karein 📥
Apne repository me ye teeno files upload karein:
* `raj_dev_renamer_bot.py` (Main bot file)
* `requirements.txt` (Telethon dependency)
* `Dockerfile` (Environment setup)

### 2. Environment Variables Set Karein ⚙️
Koyeb dashboard par **New App** banayein aur Environment Variables me ye variables add karein:
* `API_ID` = Aapka Telegram API ID
* `API_HASH` = Aapka Telegram API Hash
* `BOT_TOKEN` = BotFather se mila hua token
* `CHANNEL_ID` = Aapke channel ki ID (Jaise: `-1001234567890`)

### 3. Persistent Volume Mount (Zaroori Hai!) 💾
Koyeb me Volumes section me ja kar ye do paths ko mount karein, warna har restart par telegram login session urr jayega:
* `/app/tmp_raj_dev` (Temp files ke liye)
* `/app/session` (Telethon session data save rakhne ke liye)

---

## 🖥️ Bot Startup Logs

Bot successfully deploy hone ke baad terminal/console logs me ye show hoga:

```text
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
