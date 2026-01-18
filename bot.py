import os
import logging
import asyncio
import yt_dlp
import shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# 1. Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. .env yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 3. Video yuklash funksiyasi (yt-dlp)
def download_video(url, download_path):
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{download_path}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# 4. /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👋 Salom, **{user_name}**!\n\n"
        "🚀 Men eng tezkor **Instagram Downloader** botman.\n\n"
        "📥 Shunchaki video linkini yuboring!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# 5. Xabarlarni qayta ishlash va yuklash (Xatolik tuzatilgan qism)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if 'instagram.com' not in url:
        return 

    status_msg = await update.message.reply_text("⚡️ Tezkor yuklash boshlandi...")
    user_id = update.effective_user.id
    tmp_dir = f"tmp_{user_id}_{int(asyncio.get_event_loop().time())}"
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        # Yuklashni boshlash
        loop = asyncio.get_running_loop()
        
        # Bu yerda kod download_video tugashini kutadi (await)
        file_path = await loop.run_in_executor(None, download_video, url, tmp_dir)

        # Agar fayl muvaffaqiyatli yuklangan bo'lsa
        if file_path and os.path.exists(file_path):
            await status_msg.edit_text("📤 Telegramga yuborilmoqda...")
            with open(file_path, 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption="✅ Video tayyor!\n\n📥 Yuklovchi: @instagram_dowlander_uz_bot",
                    supports_streaming=True
                )
            await status_msg.delete()
        else:
            # Fayl yuklanmasa, xato blokiga o'tadi
            raise Exception("Fayl topilmadi")

    except Exception as e:
        logger.error(f"Yuklashda xatolik: {e}")
        # FAQAT xatolik yuz berganda shu matn chiqadi
        await status_msg.edit_text(
            "❌ Xatolik yuz berdi!\n"
            "Sababi: Video maxfiy bo'lishi yoki link noto'g'ri bo'lishi mumkin."
        )
    
    finally:
        # Vaqtinchalik fayllarni har qanday holatda tozalash
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

# 6. Python 3.14 uchun start funksiyasi
async def start_bot():
    if not BOT_TOKEN:
        print("❌ XATO: BOT_TOKEN topilmadi!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Bot Python 3.14 muhitida ishga tushdi!")
    
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        print("\n🛑 Bot to'xtatilmoqda...")
    finally:
        if app.running:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()

# 7. Ishga tushirish
if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        pass