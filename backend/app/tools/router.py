import re
from pathlib import Path

from app.tools.notes_tools import create_note
from app.tools.system_tools import (
    ensure_project_dir,
    open_app,
    open_in_vscode,
    run_npm_command,
    start_vite_dev_server,
    write_simple_html_page,
)

OPEN_PATTERNS = [
    r"^öffne\s+(.+)$",
    r"^starte\s+(.+)$",
    r"^mach\s+(.+)\s+auf$",
]

FILLER_WORDS = {
    "bitte",
    "mal",
    "das",
    "die",
    "den",
    "dem",
    "der",
    "programm",
    "app",
    "anwendung",
}


def _cleanup_app_name(text: str) -> str:
    parts = [part for part in text.strip().split() if part.lower() not in FILLER_WORDS]
    return " ".join(parts).strip()


def maybe_run_tool(user_text: str) -> str | None:
    text = user_text.lower().strip()

    if text.startswith("notiz:"):
        content = user_text.split(":", 1)[1].strip()
        if not content:
            return "Sag nach 'Notiz:' bitte auch den Inhalt dazu."
        result = create_note(content)
        return result["message"]

    if "öffne visual studio code" in text or "öffne vs code" in text or "öffne vscode" in text:
        project_dir = ensure_project_dir("jarvis-workspace")
        result = open_in_vscode(project_dir)
        return result["message"]

    if "erstelle eine simple html seite" in text or "erstelle eine einfache html seite" in text:
        project_name = "jarvis-html-page"
        result = write_simple_html_page(project_name, user_text)
        return result["message"]

    if "öffne die html seite in vscode" in text:
        project_dir = ensure_project_dir("jarvis-html-page")
        result = open_in_vscode(project_dir)
        return result["message"]

    if "npm install" in text:
        project_dir = ensure_project_dir("jarvis-html-page")
        result = run_npm_command(project_dir, ["install"])
        return result["message"]

    if "npm run dev" in text or "starte den dev server" in text:
        project_dir = ensure_project_dir("jarvis-html-page")
        result = start_vite_dev_server(project_dir)
        return result["message"]

    for pattern in OPEN_PATTERNS:
        match = re.match(pattern, text)
        if match:
            raw_target = match.group(1)
            target = _cleanup_app_name(raw_target)
            if not target:
                return "Sag mir bitte, welches Programm oder welchen Ordner ich öffnen soll."
            result = open_app(target)
            return result["message"]

    return None