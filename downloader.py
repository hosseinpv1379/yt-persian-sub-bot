import os
import uuid

import yt_dlp

from config import MAX_VIDEO_HEIGHT, MAX_VIDEO_MINUTES, WORK_DIR


class VideoTooLongError(Exception):
    pass


def probe_duration(url: str) -> float:
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return info.get("duration") or 0


def download_video(url: str) -> str:
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
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    final_path = os.path.join(WORK_DIR, f"{job_id}.mp4")
    if not os.path.exists(final_path):
        for name in os.listdir(WORK_DIR):
            if name.startswith(job_id):
                final_path = os.path.join(WORK_DIR, name)
                break
    return final_path
