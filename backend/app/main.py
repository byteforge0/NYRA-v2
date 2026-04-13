import json

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from uvicorn.protocols.utils import ClientDisconnected

from app.config import settings
from app.schemas import ChatRequest, ChatResponse
from app.services.llm import generate_reply
from app.services.stt import transcribe_wav_base64
from app.services.tts import synthesize_text
from app.tools.router import maybe_run_tool

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "app": settings.app_name,
        "env": settings.app_env,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    tool_result = maybe_run_tool(payload.text)
    if tool_result:
        return ChatResponse(reply=tool_result)

    reply = generate_reply(payload.text, payload.language_mode or "english")
    return ChatResponse(reply=reply)


async def safe_send_text(websocket: WebSocket, payload: dict) -> bool:
    try:
        await websocket.send_text(json.dumps(payload))
        return True
    except (WebSocketDisconnect, ClientDisconnected):
        return False
    except Exception as exc:
        print(f"WebSocket send error: {exc}")
        return False


async def maybe_send_tts_audio(
    websocket: WebSocket,
    text: str,
    tts_enabled: bool,
) -> bool:
    if not tts_enabled:
        return True

    try:
        result = await synthesize_text(text)
        audio_base64 = result.get("audio_base64")
        mime_type = result.get("mime_type", "audio/mpeg")

        if audio_base64:
          return await safe_send_text(
              websocket,
              {
                  "type": "assistant_audio",
                  "text": audio_base64,
                  "mime_type": mime_type,
              },
          )

        return True
    except Exception as exc:
        print(f"TTS error: {exc}")
        return await safe_send_text(
            websocket,
            {
                "type": "error",
                "text": f"TTS error: {exc}",
            },
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    try:
        await websocket.accept()
    except Exception as exc:
        print(f"WebSocket accept failed: {exc}")
        return

    if not await safe_send_text(
        websocket,
        {"type": "status", "text": "Connected to NYRA."},
    ):
        return

    try:
        while True:
            try:
                raw_message = await websocket.receive_text()
            except WebSocketDisconnect:
                print("Client disconnected.")
                return
            except Exception as exc:
                print(f"Receive error: {exc}")
                return

            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                if not await safe_send_text(
                    websocket,
                    {"type": "error", "text": "Invalid JSON received."},
                ):
                    return
                continue

            message_type = data.get("type")
            language_mode = data.get("language_mode") or "english"
            tts_enabled = bool(data.get("tts_enabled", True))

            if message_type == "ping":
                if not await safe_send_text(websocket, {"type": "pong", "text": "pong"}):
                    return
                continue

            if message_type == "stop_tts":
                continue

            if message_type == "audio_chunk":
                audio_base64 = data.get("audio_base64") or ""
                if not audio_base64:
                    if not await safe_send_text(
                        websocket,
                        {"type": "error", "text": "Empty audio data received."},
                    ):
                        return
                    continue

                if not await safe_send_text(
                    websocket,
                    {"type": "status", "text": "Listening..."},
                ):
                    return

                try:
                    user_text = transcribe_wav_base64(audio_base64)
                except Exception as exc:
                    if not await safe_send_text(
                        websocket,
                        {
                            "type": "error",
                            "text": f"Audio could not be processed: {exc}",
                        },
                    ):
                        return
                    continue

                if not user_text:
                    if not await safe_send_text(
                        websocket,
                        {
                            "type": "error",
                            "text": "I could not understand the audio clearly.",
                        },
                    ):
                        return
                    continue

                if not await safe_send_text(
                    websocket,
                    {"type": "transcript", "text": user_text},
                ):
                    return

                if not await safe_send_text(
                    websocket,
                    {"type": "status", "text": "Thinking..."},
                ):
                    return

                tool_result = maybe_run_tool(user_text)
                if tool_result:
                    if not await safe_send_text(
                        websocket,
                        {"type": "tool_result", "text": tool_result},
                    ):
                        return
                    if not await maybe_send_tts_audio(websocket, tool_result, tts_enabled):
                        return
                    continue

                reply = generate_reply(user_text, language_mode)

                if not await safe_send_text(
                    websocket,
                    {"type": "assistant_text", "text": reply},
                ):
                    return

                if not await maybe_send_tts_audio(websocket, reply, tts_enabled):
                    return
                continue

            if message_type == "user_text":
                user_text = (data.get("text") or "").strip()

                if not user_text:
                    if not await safe_send_text(
                        websocket,
                        {"type": "error", "text": "Empty message received."},
                    ):
                        return
                    continue

                if not await safe_send_text(
                    websocket,
                    {"type": "status", "text": "Thinking..."},
                ):
                    return

                tool_result = maybe_run_tool(user_text)
                if tool_result:
                    if not await safe_send_text(
                        websocket,
                        {"type": "tool_result", "text": tool_result},
                    ):
                        return
                    if not await maybe_send_tts_audio(websocket, tool_result, tts_enabled):
                        return
                    continue

                reply = generate_reply(user_text, language_mode)

                if not await safe_send_text(
                    websocket,
                    {"type": "assistant_text", "text": reply},
                ):
                    return

                if not await maybe_send_tts_audio(websocket, reply, tts_enabled):
                    return
                continue

            if not await safe_send_text(
                websocket,
                {"type": "error", "text": "Unknown message type."},
            ):
                return

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
        return
    except Exception as exc:
        print(f"Unexpected websocket error: {exc}")
        try:
            await safe_send_text(
                websocket,
                {"type": "error", "text": "Internal websocket error."},
            )
        except Exception:
            pass
        return