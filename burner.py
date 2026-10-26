import subprocess

from config import SUBTITLE_FONT


def burn_subtitles(video_path: str, srt_path: str, output_path: str):
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
    style = (
        f"FontName={SUBTITLE_FONT},FontSize=20,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=30"
    )
    vf = f"subtitles='{escaped_srt}':force_style='{style}'"
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", "20",
        "-preset", "fast",
        "-c:a", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-2000:]}")
