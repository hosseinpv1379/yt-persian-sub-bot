import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
MAX_VIDEO_MINUTES = int(os.environ.get("MAX_VIDEO_MINUTES", "20"))
MAX_VIDEO_HEIGHT = int(os.environ.get("MAX_VIDEO_HEIGHT", "720"))
SUBTITLE_FONT = os.environ.get("SUBTITLE_FONT", "Vazirmatn")
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", "1"))
WORK_DIR = os.environ.get("WORK_DIR", os.path.join(os.path.dirname(__file__), "downloads"))
PUBLIC_DIR = os.environ.get("PUBLIC_DIR", os.path.join(os.path.dirname(__file__), "public"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
FILE_RETENTION_HOURS = float(os.environ.get("FILE_RETENTION_HOURS", "24"))
