import re

YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)[\w\-]+",
    re.IGNORECASE,
)


def extract_youtube_url(text: str):
    match = YOUTUBE_RE.search(text)
    return match.group(0) if match else None
