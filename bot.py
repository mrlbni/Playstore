import os
import re
import requests
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("apkbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)"
}

def extract_package(url):
    match = re.search(r"id=([a-zA-Z0-9._]+)", url)
    return match.group(1) if match else None

def get_download_link(package):
    # apkcombo API (working)
    return f"https://apkcombo.com/api/v1/app/download?package_name={package}&device=android"

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Send Play Store link")

@app.on_message(filters.text & ~filters.command(["start"]))
async def apk_download(client, message):
    url = message.text.strip()

    if "play.google.com" not in url:
        return await message.reply_text("❌ Invalid Play Store link")

    package = extract_package(url)
    if not package:
        return await message.reply_text("❌ Package not found")

    msg = await message.reply_text("🔍 Fetching APK link...")

    try:
        api_url = get_download_link(package)
        res = requests.get(api_url, headers=HEADERS).json()

        if not res.get("ok"):
            return await msg.edit("❌ App not found")

        download_url = res["result"]["download_url"]

        file_name = f"{package}.apk"

        await msg.edit("⬇️ Downloading APK...")

        r = requests.get(download_url, headers=HEADERS, stream=True)

        total = 0
        with open(file_name, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)

        if total < 100000:  # less than 100KB = error page
            return await msg.edit("❌ Failed (blocked or invalid file)")

        await msg.edit("📤 Uploading to Telegram...")

        await client.send_document(
            message.chat.id,
            file_name,
            caption=f"✅ {package}"
        )

        os.remove(file_name)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Error:\n{str(e)}")

app.run()
