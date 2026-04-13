import base64
import io
import wave
from functools import lru_cache

import numpy as np
from faster_whisper import WhisperModel


@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    print("Lade Whisper-Modell...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("Whisper-Modell geladen.")
    return model


def transcribe_wav_base64(audio_base64: str) -> str:
    audio_bytes = base64.b64decode(audio_base64)

    with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        n_channels = wav_file.getnchannels()
        sampwidth = wav_file.getsampwidth()
        frames = wav_file.readframes(wav_file.getnframes())

    if sampwidth != 2:
        raise ValueError("Nur 16-bit PCM WAV wird unterstützt.")

    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    if n_channels == 2:
        audio = audio.reshape(-1, 2).mean(axis=1)

    model = get_model()
    segments, _ = model.transcribe(
        audio,
        language="de",
        vad_filter=True,
    )

    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text