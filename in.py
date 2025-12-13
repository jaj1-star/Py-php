import subprocess
import sys
import os

# قائمة المكتبات المطلوبة مع إصداراتها
REQUIRED_PACKAGES = [
    "python-telegram-bot==20.7",
    "yt-dlp==2024.7.23",
]

def install_packages():
    """تثبيت المكتبات المفقودة تلقائيًا"""
    import importlib.util
    success = True

    for package in REQUIRED_PACKAGES:
        package_name = package.split('==')[0]
        if importlib.util.find_spec(package_name) is None:
            print(f"📦 جاري تثبيت {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ تم تثبيت {package}")
            except subprocess.CalledProcessError:
                print(f"❌ فشل تثبيت {package}")
                success = False
        else:
            print(f"✅ {package_name} مثبت بالفعل")
    return success

# محاولة استيراد المكتبات
try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
    import yt_dlp
    print("✅ جميع المكتبات مثبتة وجاهزة")
except ImportError:
    print("🔧 بعض المكتبات غير مثبتة، جاري التثبيت التلقائي...")
    if install_packages():
        print("🔄 جاري إعادة تشغيل البرنامج بعد التثبيت...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        sys.exit(1)


BOT_TOKEN = "8527676914:AAFPjViprF4FjvrnGVfefAZN-17zNn1XatU"
DOWNLOAD_PATH = "/home/Jrogram/TelegramVideos"  # غيّر Jrogram باسم مستخدمك على PA
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً\n"
        "أرسل رابط الفيديو وأنا أنزّله لك ⬇️"
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    await update.message.reply_text("⏳ جاري التحميل...")

    ydl_opts = {  
        'outtmpl': f'{DOWNLOAD_PATH}/%(title)s.%(ext)s',  
        'format': 'bestvideo+bestaudio/best',  
        'merge_output_format': 'mp4',  
        'noplaylist': True,  
        'quiet': True,  
    }  

    try:  
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  
            info = ydl.extract_info(url, download=True)  
            file_name = ydl.prepare_filename(info)  

        await update.message.reply_video(  
            video=open(file_name, 'rb'),  
            caption="✅ تم التحميل"  
        )  
    except Exception as e:  
        await update.message.reply_text(f"❌ فشل التحميل\n{e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))  
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))  
    print("🤖 البوت شغّال...")
    app.run_polling()

if __name__ == "__main__":
    main()
