import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "JARVIS Windows DE")
    app_env: str = os.getenv("APP_ENV", "development")
    allowed_origin: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")

    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    enable_tts: bool = os.getenv("ENABLE_TTS", "true").lower() == "true"
    tts_provider: str = os.getenv("TTS_PROVIDER", "edge").lower()
    edge_tts_voice: str = os.getenv("EDGE_TTS_VOICE", "de-DE-KatjaNeural")

    projects_dir: str = os.getenv("PROJECTS_DIR", "projects")


settings = Settings()