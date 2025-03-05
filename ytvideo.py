import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext

BOT_TOKEN = "7706962104:AAEJCb2BBefKt_TGmJJJn-xt9ZzIROAODO4"  # Replace with your Telegram bot token

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me a YouTube link, and I'll download the video in your preferred quality!")

# Ask user to choose quality
def choose_quality(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    context.user_data["url"] = url  # Save URL for later use

    keyboard = [
        [InlineKeyboardButton("360p", callback_data="360p"),
         InlineKeyboardButton("480p", callback_data="480p")],
        [InlineKeyboardButton("720p", callback_data="720p"),
         InlineKeyboardButton("1080p", callback_data="1080p")],
        [InlineKeyboardButton("Highest Quality", callback_data="best")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Choose the video quality:", reply_markup=reply_markup)

# Handle quality selection
def download_video(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    quality = query.data
    url = context.user_data.get("url")

    if not url:
        query.edit_message_text("Error: No URL found. Please send the link again.")
        return

    query.edit_message_text(f"Downloading video in {quality} quality... Please wait!")

    # Mapping quality to yt-dlp format
    quality_map = {
        "360p": "bestvideo[height<=360]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "best": "bestvideo+bestaudio/best"
    }
    
    ydl_opts = {
        "format": quality_map[quality],
        "merge_output_format": "mp4",
        "outtmpl": "downloads/%(title)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        query.edit_message_text("Uploading video...")
        query.message.reply_video(video=open(file_path, "rb"), caption=f"Downloaded: {info['title']} ({quality})")

        os.remove(file_path)  # Delete file after sending

    except Exception as e:
        query.edit_message_text(f"Error: {str(e)}")

# Main function to start the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/"), choose_quality))
    dp.add_handler(CallbackQueryHandler(download_video))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
    