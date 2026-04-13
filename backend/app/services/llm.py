import requests

from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _system_prompt(language_mode: str) -> str:
    if language_mode == "german":
        return """
You are NYRA, a modern desktop voice assistant.

Rules:
- Reply in German.
- Be concise, natural, helpful, and modern.
- Do not over-explain.
- Do not produce robotic meta-commentary.
- If a tool already executed something, confirm it briefly.
- If something is not possible yet, say so clearly.
"""

    if language_mode == "auto":
        return """
You are NYRA, a modern desktop voice assistant.

Rules:
- Detect whether the user is mainly speaking English or German.
- Reply in the same language as the user.
- Be concise, natural, helpful, and modern.
- Do not over-explain.
- Do not produce robotic meta-commentary.
- If a tool already executed something, confirm it briefly.
- If something is not possible yet, say so clearly.
"""

    return """
You are NYRA, a modern desktop voice assistant.

Rules:
- Reply in English by default.
- You fully understand German too.
- If the user writes in German, you may still answer in English unless they clearly want German or language mode is german/auto.
- Be concise, natural, helpful, and modern.
- Do not over-explain.
- Do not produce robotic meta-commentary.
- If a tool already executed something, confirm it briefly.
- If something is not possible yet, say so clearly.
"""


def generate_reply(user_text: str, language_mode: str = "english") -> str:
    if not settings.openrouter_api_key:
        return (
            "I still need OPENROUTER_API_KEY in the .env file. "
            "Add it and I will answer with a real model."
        )

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "NYRA v2",
    }

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": _system_prompt(language_mode)},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.6,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        return content or "I could not generate a useful reply."
    except requests.RequestException as exc:
        return f"I could not reach OpenRouter right now. Error: {exc}"
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return f"I received an unexpected response from OpenRouter. Error: {exc}"