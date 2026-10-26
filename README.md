# ربات تلگرام دانلود یوتیوب + زیرنویس فارسی چسبیده

لینک ویدیوی یوتیوب رو برای ربات بفرست، ربات ویدیو رو دانلود می‌کند، با Whisper گفتار را به متن تبدیل می‌کند، متن را به فارسی ترجمه می‌کند، زیرنویس فارسی را با ffmpeg روی ویدیو می‌چسباند (burn-in) و فایل نهایی را برایت می‌فرستد.

## پیش‌نیاز مشترک

- توکن بات از [@BotFather](https://t.me/BotFather)

## اجرا با Docker (توصیه‌شده)

با این روش نیازی به نصب Python، ffmpeg یا فونت فارسی روی سیستم نیست؛ همه چیز داخل ایمیج ساخته می‌شود.

پیش‌نیاز: Docker و Docker Compose نصب باشند.

```bash
cd yt-persian-sub-bot
cp .env.example .env
```

توکن بات را داخل `.env` قرار بده:

```
BOT_TOKEN=123456:ABC-your-token
```

بعد بساز و اجرا کن:

```bash
docker compose up -d --build
```

لاگ‌ها:

```bash
docker compose logs -f
```

توقف:

```bash
docker compose down
```

نکات مربوط به دیتا:
- فایل‌های موقت دانلود/خروجی داخل پوشهٔ `downloads/` کنار پروژه ذخیره می‌شوند (mount شده به کانتینر).
- مدل Whisper در یک volume به نام `whisper-cache` نگه داشته می‌شود تا هر بار کانتینر بالا می‌آید دوباره دانلود نشود.
- برای ویرایش تنظیمات (مثل اندازهٔ مدل Whisper) کافیست `.env` را عوض کنی و `docker compose up -d --build` را دوباره بزنی.

## اجرای مستقیم بدون Docker (اختیاری)

اگر ترجیح می‌دهی بدون Docker اجرا کنی:

- Python 3.10+
- ffmpeg نصب‌شده روی سیستم و قابل‌دسترس در PATH (باید `libass` داشته باشد؛ بیلدهای رسمی ffmpeg این را دارند)
- یک فونت فارسی نصب‌شده که fontconfig بشناسدش، مثلاً [Vazirmatn](https://github.com/rastikerdar/vazirmatn) (برای راست‌به‌چپ و شکل درست حروف فارسی لازم است)

```bash
cd yt-persian-sub-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

توکن بات را داخل `.env` قرار بده، سپس:

```bash
python bot.py
```

سپس در تلگرام با ربات `/start` بزن و یک لینک یوتیوب برایش بفرست.

## تنظیمات (در فایل `.env`)

| متغیر | توضیح | پیش‌فرض |
|---|---|---|
| `WHISPER_MODEL_SIZE` | اندازه مدل Whisper (`tiny`/`base`/`small`/`medium`/`large-v3`) — بزرگ‌تر یعنی دقیق‌تر ولی کندتر | `small` |
| `WHISPER_DEVICE` | `cpu` یا `cuda` (اگر GPU نویدیا و cuDNN داری) | `cpu` |
| `MAX_VIDEO_MINUTES` | حداکثر طول ویدیوی قابل‌قبول | `20` |
| `MAX_VIDEO_HEIGHT` | کیفیت دانلود برای کنترل حجم فایل خروجی | `720` |
| `TELEGRAM_MAX_FILE_MB` | حداکثر حجمی که ربات حاضر است بفرستد (API معمولی تلگرام ۵۰ مگابایت محدودیت دارد) | `50` |
| `SUBTITLE_FONT` | نام فونتی که ffmpeg برای زیرنویس استفاده می‌کند | `Vazirmatn` |
| `MAX_CONCURRENT_JOBS` | تعداد پردازش هم‌زمان مجاز | `1` |

## محدودیت‌ها و نکات

- **حجم فایل:** Bot API معمولی تلگرام اجازه ارسال فایل بیشتر از ۵۰ مگابایت را نمی‌دهد. برای فایل‌های بزرگ‌تر باید یک [Local Bot API Server](https://github.com/tdlib/telegram-bot-api) خودت اجرا کنی (تا ۲ گیگابایت).
- **سرعت:** تبدیل گفتار به متن روی CPU برای ویدیوهای طولانی می‌تواند چند دقیقه طول بکشد؛ مدل `small` یا `base` برای شروع مناسب‌ترند.
- **کیفیت ترجمه:** ترجمه با Google Translate (از طریق `deep-translator`) انجام می‌شود و رایگان است، اما ممکن است گاهی محدودیت نرخ درخواست بخورد یا ترجمه کاملاً روان نباشد.
- **حقوقی:** این ابزار را فقط برای محتوایی استفاده کن که اجازهٔ دانلود/استفادهٔ شخصی یا آموزشی آن را داری و قوانین و شرایط استفادهٔ یوتیوب را در نظر بگیر.

## ساختار پروژه

```
config.py       تنظیمات از روی متغیرهای محیطی
utils.py        تشخیص لینک یوتیوب در متن پیام
downloader.py   دانلود ویدیو با yt-dlp
subtitles.py    تولید زیرنویس با faster-whisper + ترجمه به فارسی
burner.py       چسباندن زیرنویس به ویدیو با ffmpeg
bot.py          هندلرهای ربات تلگرام
Dockerfile      ایمیج شامل Python + ffmpeg + فونت Vazirmatn
docker-compose.yml   اجرای ربات با یک دستور
```
