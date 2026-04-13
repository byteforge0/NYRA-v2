from pydantic import BaseModel
from typing import Literal, Optional


class ChatRequest(BaseModel):
    text: str
    language_mode: Optional[Literal["english", "german", "auto"]] = "english"


class ChatResponse(BaseModel):
    reply: str


class WsClientMessage(BaseModel):
    type: Literal["user_text", "ping", "audio_chunk", "stop_tts"]
    text: Optional[str] = None
    audio_base64: Optional[str] = None
    language_mode: Optional[Literal["english", "german", "auto"]] = "english"
    tts_enabled: Optional[bool] = True


class WsServerMessage(BaseModel):
    type: Literal[
        "assistant_text",
        "assistant_audio",
        "tool_result",
        "status",
        "error",
        "pong",
        "transcript",
    ]
    text: str