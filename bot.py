import os
import re
import requests
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("apkbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_package(url):
    match = re.search(r"id=([a-zA-Z0-9._]+)", url)
    return match.group(1) if match else None

def get_apk_link(package):
    url = f"https://d.apkpure.com/b/APK/{package}?version=latest"
    return url

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Send Google Play Store app link 📲")

@app.on_message(filters.text & ~filters.command(["start"]))
async def download_apk(client, message):
    url = message.text.strip()
    
    if "play.google.com" not in url:
        return await message.reply_text("❌ Send valid Play Store link")

    package = extract_package(url)
    if not package:
        return await message.reply_text("❌ Invalid link")

    apk_url = get_apk_link(package)
    file_name = f"{package}.apk"

    msg = await message.reply_text("⬇️ Downloading APK...")

    try:
        r = requests.get(apk_url, stream=True)
        with open(file_name, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        await msg.edit("📤 Uploading to Telegram...")

        await client.send_document(
            chat_id=message.chat.id,
            document=file_name,
            caption=f"✅ {package}"
        )

        os.remove(file_name)

    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")

app.run()
