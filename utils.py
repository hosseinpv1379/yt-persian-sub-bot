import re
from urllib.parse import urlparse, parse_qs

URL_RE = re.compile(
    r"https?://[^\s<>]+|(?:www\.)?(?:youtu\.be|youtube\.com)/[^\s<>]+",
    re.IGNORECASE,
)
YOUTUBE_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
    "youtu.be", "www.youtu.be",
}


def extract_youtube_url(text: str):
    for match in URL_RE.finditer(text):
        candidate = match.group(0).rstrip(".,!?;:)]}\u00bb\u300b")
        if not candidate.lower().startswith(("http://", "https://")):
            candidate = "https://" + candidate
        parsed = urlparse(candidate)
        if (parsed.hostname or "").lower() not in YOUTUBE_HOSTS:
            continue
        path = parsed.path.strip("/").split("/")
        valid_video_path = (
            parsed.path == "/watch" and bool(parse_qs(parsed.query).get("v"))
        ) or (
            len(path) == 2 and path[0].lower() in {"shorts", "embed", "live"} and bool(path[1])
        ) or (parsed.hostname and parsed.hostname.lower() in {"youtu.be", "www.youtu.be"} and bool(path[0]))
        if valid_video_path:
            return candidate
    return None
