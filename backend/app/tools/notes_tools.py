from pathlib import Path
from datetime import datetime
from typing import Dict


NOTES_DIR = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)


def create_note(content: str) -> Dict[str, str]:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = NOTES_DIR / f"note_{timestamp}.md"
    path.write_text(content.strip(), encoding="utf-8")
    return {"ok": "true", "message": f"Notiz gespeichert: {path}"}