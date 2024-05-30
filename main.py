# main.py

import os
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import subprocess

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define command handlers
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me a video to start.')

def video_handler(update: Update, context: CallbackContext) -> None:
    video_file = update.message.video
    video_file.download('input_video.mp4')
    update.message.reply_text('Video received! Now send me an image or gif to use as a watermark.')

def watermark_handler(update: Update, context: CallbackContext) -> None:
    watermark_file = update.message.document or update.message.photo[-1]
    watermark_file.download('watermark.png')
    update.message.reply_text('Watermark received! Now send me the start and end times to trim the video, in seconds, separated by a space (e.g., "5 10").')

def trim_handler(update: Update, context: CallbackContext) -> None:
    times = update.message.text.split()
    if len(times) != 2:
        update.message.reply_text('Please provide exactly two numbers for the start and end times.')
        return
    
    start_time, end_time = times
    update.message.reply_text('Processing your video...')
    
    # FFmpeg command to add watermark and trim video
    command = [
        'ffmpeg', '-i', 'input_video.mp4', '-i', 'watermark.png', '-filter_complex',
        'overlay=10:10', '-ss', start_time, '-to', end_time, 'output_video.mp4'
    ]
    subprocess.run(command, check=True)
    
    update.message.reply_text('Processing completed! Sending the video back to you.')
    update.message.reply_video(video=open('output_video.mp4', 'rb'))

def main() -> None:
    # Telegram bot token from environment variable
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    PORT = int(os.environ.get('PORT', '8443'))

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.video, video_handler))
    dispatcher.add_handler(MessageHandler(Filters.document.category("image") | Filters.photo, watermark_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, trim_handler))

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.setWebhook(f"https://{os.getenv('HEROKU_APP_NAME')}.herokuapp.com/{TOKEN}")
    updater.idle()

if __name__ == '__main__':
    main()
