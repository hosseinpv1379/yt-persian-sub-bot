"""Subtitle helpers for adding downloaded tracks to media without re-encoding."""
from pathlib import Path
import subprocess


VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}


def _is_persian_track(path: Path) -> bool:
    """Recognize yt-dlp subtitle names such as ``video.fa.srt`` and
    ``video.fa-orig.vtt`` without matching unrelated words in the title.
    """
    if path.suffix.lower() not in {".srt", ".vtt"}:
        return False
    language = path.name.lower().rsplit(".", 2)[-2]
    return language == "fa" or language.startswith("fa-")


def mux_persian_subtitle(video_path: Path, subtitle_paths: list[str]) -> Path:
    """Return a Matroska copy with Persian subtitles selectable as a track.

    Video/audio streams are copied, not re-encoded. Mux failures do not break
    the media download; the original media and standalone subtitle are kept.
    """
    video_path = Path(video_path)
    if video_path.suffix.lower() not in VIDEO_EXTS:
        return video_path

    subtitle_path = next(
        (Path(p) for p in subtitle_paths if _is_persian_track(Path(p)) and Path(p).is_file()),
        None,
    )
    if subtitle_path is None:
        return video_path

    output_path = video_path.with_name(f"{video_path.stem}_fa.mkv")
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video_path),
        "-i", str(subtitle_path),
        "-map", "0:v?", "-map", "0:a?", "-map", "1:0",
        "-c", "copy", "-c:s", "srt",
        "-metadata:s:s:0", "language=fas",
        "-disposition:s:0", "default",
        str(output_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
        if result.returncode == 0 and output_path.is_file() and output_path.stat().st_size:
            return output_path
        detail = (result.stderr or "ffmpeg did not produce an output file")[-2000:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        detail = str(exc)

    output_path.unlink(missing_ok=True)
    raise RuntimeError(f"Could not mux Persian subtitles: {detail}")
