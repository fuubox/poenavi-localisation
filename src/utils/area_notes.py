import json
import os
from pathlib import Path
import tempfile

from src.utils.config_manager import ConfigManager
from src.utils.poe_version_data import POE1, POE2


SCHEMA_VERSION = 1


def notes_filename(poe_version: str) -> str:
    suffix = "poe2" if poe_version == POE2 else "poe1"
    return f"area_notes_{suffix}.json"


def notes_path(poe_version: str) -> Path:
    return ConfigManager.get_user_data_path(notes_filename(poe_version))


def load_area_notes(poe_version: str) -> dict[str, str]:
    path = notes_path(poe_version)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"エリアメモを読み込めません: {path}") from exc
    raw_notes = payload.get("notes", {}) if isinstance(payload, dict) else {}
    if not isinstance(raw_notes, dict):
        raise ValueError(f"エリアメモの形式が不正です: {path}")
    return {
        str(zone_id): content
        for zone_id, content in raw_notes.items()
        if isinstance(content, str) and content.strip()
    }


def save_area_notes(poe_version: str, notes: dict[str, str]) -> Path:
    path = notes_path(poe_version)
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = {
        str(zone_id): content.strip()
        for zone_id, content in notes.items()
        if isinstance(content, str) and content.strip()
    }
    payload = {"schema": SCHEMA_VERSION, "notes": cleaned}
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return path


def get_area_note(poe_version: str, zone_id: str | None) -> str:
    if not zone_id:
        return ""
    return load_area_notes(poe_version).get(zone_id, "")


def set_area_note(poe_version: str, zone_id: str, content: str) -> Path:
    if not zone_id:
        raise ValueError("エリアIDがありません")
    notes = load_area_notes(poe_version)
    if content.strip():
        notes[zone_id] = content.strip()
    else:
        notes.pop(zone_id, None)
    return save_area_notes(poe_version, notes)
