import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "9102484338:AAFxo-u9DJH4ydigqsQl1TbqBcWF6QC__Zo")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hallo! Sende mir den Link zu einem TikTok-Profil (z. B. https://www.tiktok.com/@username), "
        "und ich lade alle öffentlich verfügbaren Videos für dich herunter!"
    )

async def download_tiktok_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "tiktok.com/" not in url:
        await update.message.reply_text("Bitte sende einen gültigen TikTok-Link.")
        return

    status_msg = await update.message.reply_text("Analysiere Profil und starte Download...")

    download_folder = f"downloads_{update.message.chat_id}"
    os.makedirs(download_folder, exist_ok=True)

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{download_folder}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    try:
        loop = asyncio.get_running_loop()
        
        def fetch_and_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        info = await loop.run_in_executor(None, fetch_and_download)

        if not info:
            await status_msg.edit_text("Es konnten keine Videos gefunden werden.")
            return

        files = [os.path.join(download_folder, f) for f in os.listdir(download_folder) if f.endswith(('.mp4', '.mkv'))]
        
        await status_msg.edit_text(f"{len(files)} Video(s) gefunden. Sende Dateien...")

        for file_path in files:
            try:
                with open(file_path, 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=video_file
                    )
            except Exception as e:
                logging.error(f"Fehler beim Senden von {file_path}: {e}")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        await update.message.reply_text("Alle Downloads abgeschlossen!")

    except Exception as e:
        await status_msg.edit_text(f"Fehler aufgetreten: {str(e)}")
    finally:
        if os.path.exists(download_folder):
            for f in os.listdir(download_folder):
                os.remove(os.path.join(download_folder, f))
            os.rmdir(download_folder)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok_profile))
    
    print("Bot läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()
