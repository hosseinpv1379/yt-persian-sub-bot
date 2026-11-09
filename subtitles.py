import datetime
import threading
import time

import srt
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests
from faster_whisper import WhisperModel

from config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL_SIZE

_model = None
_translation_lock = threading.Lock()
_last_translation_request = 0.0
_MIN_TRANSLATION_INTERVAL = 0.5
_RATE_LIMIT_RETRY_DELAYS = (2, 4, 8, 16, 30)


class TranslationRateLimitError(RuntimeError):
    pass


def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)
    return _model


def transcribe(video_path: str):
    model = _get_model()
    segments, _ = model.transcribe(video_path, vad_filter=True)
    return [(seg.start, seg.end, seg.text.strip()) for seg in segments if seg.text.strip()]


def translate_to_persian(segments):
    global _last_translation_request

    translator = GoogleTranslator(source="auto", target="fa")
    translated = []
    for start, end, text in segments:
        fa_text = None
        with _translation_lock:
            for attempt in range(len(_RATE_LIMIT_RETRY_DELAYS) + 1):
                wait = _MIN_TRANSLATION_INTERVAL - (time.monotonic() - _last_translation_request)
                if wait > 0:
                    time.sleep(wait)
                try:
                    fa_text = translator.translate(text)
                    _last_translation_request = time.monotonic()
                    break
                except TooManyRequests as exc:
                    _last_translation_request = time.monotonic()
                    if attempt == len(_RATE_LIMIT_RETRY_DELAYS):
                        raise TranslationRateLimitError(
                            "ترجمه پس از چند تلاش هنوز با محدودیت نرخ مواجه است؛ کمی بعد دوباره تلاش کنید."
                        ) from exc
                    time.sleep(_RATE_LIMIT_RETRY_DELAYS[attempt])
                except Exception as exc:
                    raise RuntimeError("ترجمهٔ زیرنویس انجام نشد؛ سرویس ترجمه را بررسی کنید.") from exc
        if not fa_text:
            raise RuntimeError("سرویس ترجمه برای بخشی از زیرنویس پاسخ خالی داد.")
        translated.append((start, end, fa_text))
    return translated


def write_srt(segments, srt_path: str):
    subs = [
        srt.Subtitle(
            index=i,
            start=datetime.timedelta(seconds=start),
            end=datetime.timedelta(seconds=end),
            content=text,
        )
        for i, (start, end, text) in enumerate(segments, start=1)
    ]
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))
