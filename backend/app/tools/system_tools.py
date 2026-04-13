import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

from app.config import settings


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )


def _which(executable: str) -> Optional[str]:
    found = shutil.which(executable)
    return found


def _existing_path(paths: list[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists():
            return path
    return None


def _start_path(path: Path) -> bool:
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
        return True
    except Exception:
        return False


def _common_windows_paths() -> dict[str, list[Path]]:
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    appdata = Path(os.environ.get("APPDATA", ""))
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    user = Path.home()

    return {
        "steam": [
            program_files_x86 / "Steam" / "steam.exe",
            program_files / "Steam" / "steam.exe",
            user / "AppData" / "Local" / "Programs" / "Steam" / "steam.exe",
        ],
        "obsidian": [
            local / "Obsidian" / "Obsidian.exe",
            user / "AppData" / "Local" / "Obsidian" / "Obsidian.exe",
        ],
        "vscode": [
            local / "Programs" / "Microsoft VS Code" / "Code.exe",
            program_files / "Microsoft VS Code" / "Code.exe",
            program_files_x86 / "Microsoft VS Code" / "Code.exe",
        ],
        "chrome": [
            program_files / "Google" / "Chrome" / "Application" / "chrome.exe",
            program_files_x86 / "Google" / "Chrome" / "Application" / "chrome.exe",
            local / "Google" / "Chrome" / "Application" / "chrome.exe",
        ],
        "edge": [
            program_files_x86 / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            program_files / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ],
        "discord": [
            local / "Discord" / "Update.exe",
        ],
        "spotify": [
            appdata / "Spotify" / "Spotify.exe",
            local / "Microsoft" / "WindowsApps" / "Spotify.exe",
        ],
    }


def open_app(target: str) -> Dict[str, str]:
    clean = target.strip().lower()

    alias_map = {
        "notepad": "notepad.exe",
        "editor": "notepad.exe",
        "rechner": "calc.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "explorer": "explorer.exe",
        "datei explorer": "explorer.exe",
        "terminal": "powershell.exe",
        "powershell": "powershell.exe",
        "cmd": "cmd.exe",
        "steam": "steam.exe",
        "obsidian": "obsidian.exe",
        "vscode": "Code.exe",
        "vs code": "Code.exe",
        "visual studio code": "Code.exe",
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "spotify": "Spotify.exe",
        "discord": "Discord.exe",
    }

    # 1) Explizite Windows-Systemapps
    executable = alias_map.get(clean)
    if executable and _which(executable):
        try:
            subprocess.Popen([executable])
            return {"ok": "true", "message": f"Ich habe {target} geöffnet."}
        except Exception as exc:
            return {"ok": "false", "message": f"Fehler beim Öffnen von {target}: {exc}"}

    # 2) Bekannte Installationspfade
    known_paths = _common_windows_paths()
    if clean in known_paths:
        found_path = _existing_path(known_paths[clean])
        if found_path and _start_path(found_path):
            return {"ok": "true", "message": f"Ich habe {target} geöffnet."}

    # 3) Direkte Pfadangabe
    possible_path = Path(target).expanduser()
    if possible_path.exists() and _start_path(possible_path):
        return {"ok": "true", "message": f"Ich habe {target} geöffnet."}

    # 4) Explorer-Laufwerk wie C:
    if len(clean) == 2 and clean[1] == ":":
        try:
            subprocess.Popen(["explorer.exe", clean])
            return {"ok": "true", "message": f"Ich habe {target} geöffnet."}
        except Exception as exc:
            return {"ok": "false", "message": f"Fehler beim Öffnen von {target}: {exc}"}

    # 5) Letzter Versuch über startfile / Shell
    if executable:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", executable], shell=False)
            return {"ok": "true", "message": f"Ich versuche, {target} zu öffnen."}
        except Exception:
            pass

    return {
        "ok": "false",
        "message": (
            f"Ich konnte {target} nicht finden. "
            "Wenn du willst, erweitere ich die App-Suche noch mit Startmenü-Shortcuts."
        ),
    }


def ensure_project_dir(project_name: str) -> Path:
    safe_name = "".join(ch for ch in project_name if ch.isalnum() or ch in ("-", "_", " ")).strip()
    safe_name = safe_name.replace(" ", "-") or "new-project"

    base_dir = Path(settings.projects_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    project_dir = base_dir / safe_name
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def open_in_vscode(project_dir: Path) -> Dict[str, str]:
    code_candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Microsoft VS Code" / "Code.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft VS Code" / "Code.exe",
    ]

    code_path = _existing_path(code_candidates)
    if code_path is None and _which("Code.exe"):
        code_path = Path(_which("Code.exe") or "")

    if code_path is None:
        return {
            "ok": "false",
            "message": "Visual Studio Code wurde nicht gefunden.",
        }

    try:
        subprocess.Popen([str(code_path), str(project_dir)])
        return {"ok": "true", "message": f"Ich habe VS Code für {project_dir} geöffnet."}
    except Exception as exc:
        return {"ok": "false", "message": f"VS Code konnte nicht geöffnet werden: {exc}"}


def write_simple_html_page(project_name: str, prompt: str) -> Dict[str, str]:
    project_dir = ensure_project_dir(project_name)
    html_path = project_dir / "index.html"

    html = f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
    <style>
      body {{
        margin: 0;
        font-family: Inter, Arial, sans-serif;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: #0f172a;
        color: white;
      }}
      .card {{
        padding: 32px;
        border-radius: 20px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        max-width: 720px;
      }}
      h1 {{ margin-top: 0; }}
      p {{ line-height: 1.6; }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>{project_name}</h1>
      <p>Diese Seite wurde von JARVIS erzeugt.</p>
      <p>Beschreibung: {prompt}</p>
    </div>
  </body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")

    return {
        "ok": "true",
        "message": f"Ich habe eine einfache HTML-Seite in {html_path} erstellt.",
    }


def run_npm_command(project_dir: Path, command: list[str]) -> Dict[str, str]:
    npm_path = _which("npm.cmd") or _which("npm")
    if not npm_path:
        return {"ok": "false", "message": "npm wurde nicht gefunden."}

    try:
        result = subprocess.run(
            [npm_path, *command],
            cwd=project_dir,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
    except Exception as exc:
        return {"ok": "false", "message": f"npm konnte nicht ausgeführt werden: {exc}"}

    if result.returncode != 0:
        return {
            "ok": "false",
            "message": f"npm {' '.join(command)} fehlgeschlagen: {result.stderr or result.stdout}",
        }

    return {
        "ok": "true",
        "message": f"npm {' '.join(command)} wurde in {project_dir} ausgeführt.",
    }


def start_vite_dev_server(project_dir: Path) -> Dict[str, str]:
    npm_path = _which("npm.cmd") or _which("npm")
    if not npm_path:
        return {"ok": "false", "message": "npm wurde nicht gefunden."}

    try:
        subprocess.Popen(
            [npm_path, "run", "dev"],
            cwd=project_dir,
            shell=False,
        )
        return {
            "ok": "true",
            "message": f"Ich habe den Dev-Server in {project_dir} gestartet.",
        }
    except Exception as exc:
        return {
            "ok": "false",
            "message": f"Dev-Server konnte nicht gestartet werden: {exc}",
        }