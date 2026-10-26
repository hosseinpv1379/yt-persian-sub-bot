import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from yt_dlp.utils import DownloadError
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from burner import burn_subtitles
from cleanup import cleanup_old_files
from config import (
    BOT_TOKEN,
    FILE_RETENTION_HOURS,
    MAX_CONCURRENT_JOBS,
    PUBLIC_BASE_URL,
    PUBLIC_DIR,
)
from downloader import VideoTooLongError, download_video
from subtitles import transcribe, translate_to_persian, write_srt
from utils import extract_youtube_url

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_JOBS)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! لینک ویدیوی یوتیوب رو برام بفرست تا دانلودش کنم و با زیرنویس فارسی چسبیده برات بفرستم."
    )


def _process(url: str, status_cb) -> str:
    status_cb("در حال دانلود ویدیو...")
    video_path = download_video(url)
    job_id = os.path.splitext(os.path.basename(video_path))[0]

    status_cb("در حال تشخیص گفتار و تولید زیرنویس...")
    segments = transcribe(video_path)

    status_cb("در حال ترجمه زیرنویس به فارسی...")
    fa_segments = translate_to_persian(segments)

    srt_path = video_path.rsplit(".", 1)[0] + ".srt"
    write_srt(fa_segments, srt_path)

    status_cb("در حال چسباندن زیرنویس به ویدیو...")
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    output_path = os.path.join(PUBLIC_DIR, f"{job_id}_fa.mp4")
    burn_subtitles(video_path, srt_path, output_path)

    for path in (video_path, srt_path):
        try:
            os.remove(path)
        except OSError:
            pass

    return output_path


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    url = extract_youtube_url(text)
    if not url:
        await update.message.reply_text("لطفاً یک لینک معتبر یوتیوب بفرست.")
        return

    status_message = await update.message.reply_text("درخواست دریافت شد، در صف پردازش قرار گرفت...")
    loop = asyncio.get_running_loop()

    def status_cb(msg: str):
        async def _edit():
            try:
                await status_message.edit_text(msg)
            except Exception:
                pass

        asyncio.run_coroutine_threadsafe(_edit(), loop)

    try:
        output_path = await loop.run_in_executor(executor, _process, url, status_cb)
    except VideoTooLongError as e:
        await status_message.edit_text(str(e))
        return
    except DownloadError as e:
        logger.warning("video download failed: %s", e)
        if "sign in to confirm" in str(e).lower():
            await status_message.edit_text(
                "یوتیوب از سرور درخواست تأیید ورود کرده است. مدیر ربات باید فایل کوکی یوتیوب را تنظیم کند و دوباره تلاش کنید."
            )
        else:
            await status_message.edit_text("دانلود ویدیو از یوتیوب ناموفق بود. لطفاً بعداً دوباره تلاش کنید.")
        return
    except Exception:
        logger.exception("processing failed")
        await status_message.edit_text("خطا در پردازش ویدیو. لطفاً به مدیر ربات اطلاع دهید.")
        return

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    link = f"{PUBLIC_BASE_URL}/{os.path.basename(output_path)}"
    await status_message.edit_text(
        "ویدیو آماده شد ✅ (به‌خاطر محدودیت حجم فایل در تلگرام، به‌جای ارسال مستقیم، لینک دانلود می‌فرستم):\n\n"
        f"{link}\n\n"
        f"حجم فایل: {size_mb:.1f} مگابایت\n"
        f"این لینک حدود {FILE_RETENTION_HOURS:.0f} ساعت دیگر معتبر است، پس زودتر دانلودش کن."
    )


async def _cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    cleanup_old_files(PUBLIC_DIR, FILE_RETENTION_HOURS)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است. آن را در فایل .env قرار دهید.")
    if not PUBLIC_BASE_URL:
        raise RuntimeError(
            "PUBLIC_BASE_URL تنظیم نشده است. آدرسی که وب‌سرور فایل‌ها از آن در دسترس است را در .env بگذار "
            "(مثلاً http://SERVER_IP:8080)."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(_cleanup_job, interval=3600, first=60)
    app.run_polling()


if __name__ == "__main__":
    main()
