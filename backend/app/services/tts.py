import base64
import tempfile
from pathlib import Path

import edge_tts

from app.config import settings


async def synthesize_text(text: str) -> dict:
    if not settings.enable_tts:
        return {
            "ok": True,
            "text": text,
            "skipped": True,
            "provider": "disabled",
        }

    if settings.tts_provider != "edge":
        raise RuntimeError(
            f"Unknown TTS_PROVIDER: {settings.tts_provider}. "
            "Set TTS_PROVIDER=edge in the .env."
        )

    if not text.strip():
        return {
            "ok": True,
            "text": text,
            "skipped": True,
            "provider": "edge",
        }

    out_path = Path(tempfile.gettempdir()) / "nyra_edge_tts.mp3"

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=settings.edge_tts_voice,
        )
        await communicate.save(str(out_path))
        audio_bytes = out_path.read_bytes()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"Edge TTS failed: {exc}") from exc

    return {
        "ok": True,
        "text": text,
        "provider": "edge",
        "mime_type": "audio/mpeg",
        "audio_base64": audio_base64,
        "voice": settings.edge_tts_voice,
    }