import os
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.storage import MemoryStorage

# ---------------------------------------------------
#   1) Telegram API Credentials (REPLACE THESE)
# ---------------------------------------------------
API_ID = 1234567  # e.g., 1234567
API_HASH = "abcdef1234567890abcdef1234567890"  # e.g., "abcdef1234567890abcdef1234567890"
BOT_TOKEN = "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # e.g., "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# ---------------------------------------------------
#   2) Prevent SQLite lock by removing old session
# ---------------------------------------------------
if os.path.exists("youtube_downloader.session"):
    os.remove("youtube_downloader.session")

# ---------------------------------------------------
#   3) Initialize the Bot with Memory Storage
# ---------------------------------------------------
bot = Client(
    "youtube_downloader",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    storage=MemoryStorage()  # Avoids "database is locked" errors
)

# ---------------------------------------------------
#   4) Quality Formats Dictionary
# ---------------------------------------------------
QUALITY_FORMATS = {
    "360":    "bestvideo[height<=360]+bestaudio/best",
    "480":    "bestvideo[height<=480]+bestaudio/best",
    "720":    "bestvideo[height<=720]+bestaudio/best",
    "1080":   "bestvideo[height<=1080]+bestaudio/best",
    "highest": "bestvideo+bestaudio/best"
}

def get_format_string(desired_quality: str) -> str:
    """
    Returns the yt-dlp format string based on the desired quality.
    If the user-specified quality isn't recognized, defaults to 'highest'.
    """
    desired_quality = desired_quality.lower()
    return QUALITY_FORMATS.get(desired_quality, QUALITY_FORMATS["highest"])

# ---------------------------------------------------
#   5) Helper: Download and Send Video
# ---------------------------------------------------
async def download_and_send_video(client, message, url, quality="highest"):
    """
    Downloads the video from 'url' using 'quality' and sends it back to the user.
    """
    await message.reply_text(f"🎥 Downloading in *{quality}* quality... Please wait.")

    ydl_opts = {
        "format": get_format_string(quality),
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            # Ensure .mp4 extension if missing
            if "." not in file_path.split("/")[-1]:
                file_path += ".mp4"

        # Send the video to the user
        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"✅ Here is your video ({quality.upper()} quality)!"
        )

        # Remove the file after sending
        os.remove(file_path)

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# ---------------------------------------------------
#   6) Handlers
# ---------------------------------------------------

# /start - Greeting
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "Hello! I'm a YouTube Downloader Bot.\n\n"
        "Send me a YouTube link directly, or use:\n"
        "`/download <resolution> <URL>`.\n\n"
        "Example:\n`/download 720 https://youtu.be/...`\n"
        "Available resolutions: 360, 480, 720, 1080, highest."
    )

# /help - Instructions
@bot.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply_text(
        "🔹 *YouTube Video Downloader Bot*\n\n"
        "**How to Use:**\n"
        "1. Send a YouTube link directly (downloads highest quality).\n"
        "2. Use `/download <resolution> <URL>`:\n"
        "   - Resolutions: 360, 480, 720, 1080, highest\n\n"
        "**Examples:**\n"
        "`/download https://youtu.be/XXXX` (highest)\n"
        "`/download 480 https://youtu.be/XXXX` (480p)\n"
        "`/download highest https://youtu.be/XXXX` (max possible)\n"
        "Enjoy!"
    )

# /download - Main download command
@bot.on_message(filters.command("download"))
async def download_command(client, message):
    parts = message.text.split(maxsplit=2)

    # If user only typed "/download"
    if len(parts) < 2:
        await message.reply_text(
            "❌ You didn't provide a link.\n\n"
            "Usage:\n`/download <URL>` (highest)\n"
            "`/download <quality> <URL>` (360/480/720/1080/highest)"
        )
        return

    # /download <URL>  => highest
    if len(parts) == 2:
        url = parts[1]
        await download_and_send_video(client, message, url, "highest")
        return

    # /download <quality> <URL>
    quality_candidate = parts[1].lower()
    url = parts[2]
    if quality_candidate in QUALITY_FORMATS:
        await download_and_send_video(client, message, url, quality_candidate)
    else:
        await message.reply_text(
            f"❌ Unrecognized resolution *{quality_candidate}*.\n"
            "Available: 360, 480, 720, 1080, highest.\n\n"
            "Usage:\n`/download <resolution> <YouTube URL>`"
        )

# Direct link detection (no command)
@bot.on_message(filters.regex(r"https?://(www\.)?(youtube\.com|youtu\.be)/.+"))
async def direct_link_handler(client, message):
    url = message.text.strip()
    # Default to highest if user sends a direct YouTube link
    await download_and_send_video(client, message, url, "highest")

# ---------------------------------------------------
#   7) Run the Bot (main entry)
# ---------------------------------------------------
async def run_bot():
    await bot.start()
    print("🚀 Bot is running... Press Ctrl+C to stop.")
    await asyncio.Event().wait()  # Keep it running

if __name__ == "__main__":
    asyncio.run(run_bot())