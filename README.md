# 🌌 Raj Dev - Channel File Renamer Bot

Telegram channel me ek sath aane wali bhot saari files (videos, documents, audio) ko auto-rename karne ke liye ek advanced aur fast bot.

<div align="center">
  <table style="border: none; border-collapse: collapse; margin: 20px auto;">
    <tr>
      <td style="background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); padding: 6px; border-radius: 20px; box-shadow: 0px 20px 50px rgba(0, 242, 254, 0.45);">
        <img src="https://i.ibb.co/qFyMDRk8/IMG-20251130-WA0108-2.jpg" width="750" style="border-radius: 15px; display: block;" alt="Raj Dev Banner">
      </td>
    </tr>
  </table>

  <br>

  [Telegram Profile](https://t.me/raj_dev_01) • [Instagram Profile](https://instagram.com/itz_dminem_official43) • [Telegram Channel](https://t.me/raj_dev_01)
</div>

---

## 🛠️ Yeh Bot Kaise Kaam Karta Hai?

1. **Auto-Fetch:** Jab bhi aap apne channel me koi file upload ya forward karoge, bot use turant detect kar lega.
2. **Auto-Rename:** Bot file ka original name nikalega aur uske aage aapka naam jod dega: `Raj Dev - [Original_Name].[ext]`.
3. **Parallel Processing:** Agar aap ek sath 25-30 files bhi daloge, toh bot queue bana kar sabko ek sath process karega (Bot hang nahi hoga).
4. **Auto-Clean:** File rename karke wapas channel me upload hote hi, bot purani bina-rename wali file ko channel se delete kar dega taaki double post na ho. Sath hi local server se bhi file delete ho jayegi taaki storage full na ho.
5. **Security:** Developer ka credit block Base64 aur SHA-256 se hardcoded locked hai. Agar koi naam hatane ki koshish karega toh bot chalega hi nahi.

---

## 🚀 Koyeb / Render Deployment Steps

Is bot ko cloud par 24/7 live rakhne ke liye ye simple steps follow karein:

### 1. GitHub me Files Push Karein
Apne repository me ye teeno files upload karein:
* `raj_dev_renamer_bot.py` (Main bot file)
* `requirements.txt` (Telethon dependency)
* `Dockerfile` (Environment setup)

### 2. Environment Variables Set Karein
Koyeb dashboard par **New App** banayein aur Environment Variables me ye variables add karein:
* `API_ID` = Aapka Telegram API ID
* `API_HASH` = Aapka Telegram API Hash
* `BOT_TOKEN` = BotFather se mila hua token
* `CHANNEL_ID` = Aapke channel ki ID (Jaise: `-1001234567890`)

### 3. Persistent Volume Mount (Zaroori Hai!)
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
