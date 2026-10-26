import datetime

import srt
from deep_translator import GoogleTranslator
from faster_whisper import WhisperModel

from config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL_SIZE

_model = None


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
    translator = GoogleTranslator(source="auto", target="fa")
    translated = []
    for start, end, text in segments:
        try:
            fa_text = translator.translate(text)
        except Exception:
            fa_text = text
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
