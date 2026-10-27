"""Validated environment configuration; all application data stays in this project."""
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    database_path: Path
    llm_enabled: bool = False
    llm_api_key: str = field(default="", repr=False)
    llm_model: str = ""

    llm_timeout_seconds: int = 20
    demo_mode: bool = False
    encryption_keys: str = field(default="", repr=False)
    legacy_local: bool = False

    @property
    def llm_ready(self) -> bool:
        return self.llm_enabled and bool(self.llm_api_key and self.llm_model)


def load_settings(env=None) -> Settings:
    if env is None:
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        env = os.environ
    raw = env.get("MINDMATE_DB_PATH", "data/mindmate.sqlite3").strip()
    if not raw:
        raise ValueError("MINDMATE_DB_PATH must not be empty")
    # Reject network/device paths before resolve() can probe a UNC share on Windows.
    win = PureWindowsPath(raw)
    if raw.startswith(("\\\\", "//")) or (win.drive and (not win.root or win.drive.casefold() != PureWindowsPath(PROJECT_ROOT).drive.casefold())):
        raise ValueError("Database path must be a local project file")
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}
    if any(part.split(".")[0].upper() in reserved or part.endswith((" ", ".")) and part not in {".", ".."} or (":" in part and part != win.anchor and part != win.drive) for part in win.parts):
        raise ValueError("Unsupported database filename")
    candidate = PROJECT_ROOT / raw
    if candidate.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("Database filename must end in .db, .sqlite or .sqlite3")
    if any(part.casefold() in {".git", ".agents", ".codex", ".aws", ".venv"} for part in candidate.parts):
        raise ValueError("Database path must not use a protected project directory")
    path = candidate.resolve()
    if any(part.casefold() in {".git", ".agents", ".codex", ".aws", ".venv"} for part in path.parts):
        raise ValueError("Database path must not use a protected project directory")
    if not path.is_relative_to(PROJECT_ROOT) or path == PROJECT_ROOT:
        raise ValueError("Database path must be a file inside the MindMate-AI folder")
    flag = env.get("MINDMATE_LLM_ENABLED", "false").strip().lower()
    if flag not in {"true", "false"}:
        raise ValueError("MINDMATE_LLM_ENABLED must be true or false")
    try:
        timeout = int(env.get("MINDMATE_LLM_TIMEOUT_SECONDS", "20"))
        if not 1 <= timeout <= 60:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError("MINDMATE_LLM_TIMEOUT_SECONDS must be an integer from 1 to 60") from None
    demo = env.get("MINDMATE_DEMO_MODE", "false").strip().lower()
    if demo not in {"true", "false"}:
        raise ValueError("MINDMATE_DEMO_MODE must be true or false")
    legacy = env.get("MINDMATE_LEGACY_LOCAL", "false").strip().lower()
    if legacy not in {"true","false"}:
        raise ValueError("MINDMATE_LEGACY_LOCAL must be true or false")
    return Settings(path, flag == "true", env.get("MINDMATE_LLM_API_KEY", "").strip(),
                    env.get("MINDMATE_LLM_MODEL", "").strip(), timeout, demo == "true", env.get("MINDMATE_ENCRYPTION_KEYS", "").strip(), legacy == "true")
