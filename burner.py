import subprocess

def mux_subtitles(video_path: str, srt_path: str, output_path: str):
    """Add selectable SRT subtitles without re-encoding video or audio."""
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", video_path,
        "-i", srt_path,
        "-map", "0",
        "-map", "1:0",
        "-c", "copy",
        "-c:s", "srt",
        "-metadata:s:s:0", "language=fas",
        "-disposition:s:s:0", "default",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-2000:]}")
