import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager

import yt_dlp

from config import MAX_VIDEO_HEIGHT, MAX_VIDEO_MINUTES, WORK_DIR, YT_DLP_COOKIES_FILE


class VideoTooLongError(Exception):
    pass


class PersianSubtitlesUnavailableError(Exception):
    pass


@contextmanager
def _youtube_dl(options: dict):
    options = {"quiet": True, "noplaylist": True, **options}
    # yt-dlp saves its cookie jar on close, so keep the mounted source read-only.
    with tempfile.TemporaryDirectory() as temp_dir:
        if YT_DLP_COOKIES_FILE:
            if not os.path.isfile(YT_DLP_COOKIES_FILE):
                raise FileNotFoundError(
                    f"YT_DLP_COOKIES_FILE is set, but the file is missing: {YT_DLP_COOKIES_FILE}"
                )
            cookie_copy = os.path.join(temp_dir, "cookies.txt")
            shutil.copyfile(YT_DLP_COOKIES_FILE, cookie_copy)
            options["cookiefile"] = cookie_copy
        with yt_dlp.YoutubeDL(options) as ydl:
            yield ydl


def probe_duration(url: str) -> float:
    with _youtube_dl({}) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise yt_dlp.utils.DownloadError("yt-dlp could not read video information")
    # Some extractors return a playlist-like object despite noplaylist. Prefer
    # the selected video's duration when available.
    if info.get("_type") == "playlist":
        entries = info.get("entries") or []
        info = next((entry for entry in entries if entry), {})
    return float(info.get("duration") or 0)


def download_video_with_persian_subtitle(url: str) -> tuple[str, str]:
    duration = probe_duration(url)
    if duration and duration > MAX_VIDEO_MINUTES * 60:
        raise VideoTooLongError(
            f"ویدیو {duration / 60:.1f} دقیقه است و از حد مجاز ({MAX_VIDEO_MINUTES} دقیقه) بیشتر است."
        )

    os.makedirs(WORK_DIR, exist_ok=True)
    job_id = uuid.uuid4().hex[:10]
    out_template = os.path.join(WORK_DIR, f"{job_id}.%(ext)s")

    ydl_opts = {
        "format": f"bestvideo[height<={MAX_VIDEO_HEIGHT}]+bestaudio/best[height<={MAX_VIDEO_HEIGHT}]",
        "merge_output_format": "mp4",
        "outtmpl": out_template,
        # YouTube's android_vr player has recently returned truncated media
        # responses (often followed by HTTP 503). Keep the normal web clients
        # and explicitly exclude that unstable client.
        "extractor_args": {
            "youtube": {"player_client": ["default", "web_embedded", "-android_vr"]}
        },
        # Retry temporary CDN/network failures without retrying forever.
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 5,
        # Prefer a creator-provided Persian track, then YouTube's Persian
        # auto-caption/auto-translation track when one is available.
        "writesubtitles": True,
        "writeautomaticsub": True,
        # Request only the needed language; broad regexes can request extra
        # translated tracks and trigger YouTube's subtitle rate limit.
        "subtitleslangs": ["fa"],
        "subtitlesformat": "srt/best",
        "convertsubtitles": "srt",
        # YouTube commonly rate-limits auto-translated tracks unless requests
        # are spaced well apart.
        "sleep_interval_requests": 1,
        "sleep_interval_subtitles": 60,
    }
    try:
        with _youtube_dl(ydl_opts) as ydl:
            result = ydl.download([url])

        if result:
            raise yt_dlp.utils.DownloadError("yt-dlp could not download the requested video")

        final_path = os.path.join(WORK_DIR, f"{job_id}.mp4")
        if not os.path.isfile(final_path):
            matches = [
                os.path.join(WORK_DIR, name)
                for name in os.listdir(WORK_DIR)
                if name.startswith(f"{job_id}.") and os.path.isfile(os.path.join(WORK_DIR, name))
            ]
            if not matches:
                raise yt_dlp.utils.DownloadError("yt-dlp finished without producing a video file")
            final_path = matches[0]

        subtitle_matches = sorted(
            os.path.join(WORK_DIR, name)
            for name in os.listdir(WORK_DIR)
            if name.startswith(f"{job_id}.fa") and name.lower().endswith(".srt")
        )
        if not subtitle_matches:
            raise PersianSubtitlesUnavailableError(
                "This video does not expose Persian subtitles or a Persian auto-translated track through YouTube."
            )
        subtitle_matches.sort(key=lambda path: 0 if os.path.basename(path) == f"{job_id}.fa.srt" else 1)
        return final_path, subtitle_matches[0]
    except Exception:
        for name in os.listdir(WORK_DIR):
            if name.startswith(f"{job_id}."):
                try:
                    os.remove(os.path.join(WORK_DIR, name))
                except OSError:
                    pass
        raise
