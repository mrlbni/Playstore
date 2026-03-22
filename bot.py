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


def get_apkcombo_link(package):
    return f"https://apkcombo.com/api/v1/app/download?package_name={package}&device=android"


def fallback_apkpure(package):
    return f"https://d.apkpure.com/b/APK/{package}?version=latest"


@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Send Play Store link")


@app.on_message(filters.text & ~filters.command(["start"]))
async def download(client, message):
    url = message.text.strip()

    if "play.google.com" not in url:
        return await message.reply_text("❌ Invalid Play Store link")

    package = extract_package(url)
    if not package:
        return await message.reply_text("❌ Package not found")

    msg = await message.reply_text("🔍 Fetching download link...")

    download_url = None

    try:
        # Try APKCombo API
        api_url = get_apkcombo_link(package)
        res = requests.get(api_url, headers=HEADERS)

        if "application/json" in res.headers.get("Content-Type", ""):
            data = res.json()
            if data.get("ok"):
                download_url = data["result"]["download_url"]

    except:
        pass

    # Fallback to APKPure
    if not download_url:
        download_url = fallback_apkpure(package)

    file_name = f"{package}.apk"

    await msg.edit("⬇️ Downloading APK...")

    try:
        r = requests.get(download_url, headers=HEADERS, stream=True)

        total = 0
        with open(file_name, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)

        # Check valid file
        if total < 100000:
            return await msg.edit("❌ Failed: blocked or invalid APK")

        await msg.edit("📤 Uploading...")

        await client.send_document(
            message.chat.id,
            file_name,
            caption=f"✅ {package}"
        )

        os.remove(file_name)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Download Error:\n{str(e)}")


app.run()
