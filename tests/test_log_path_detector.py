from pathlib import Path

from src.utils import log_path_detector as detector


def test_detect_client_log_paths_prefers_steam_library(tmp_path, monkeypatch):
    steam = tmp_path / "Steam"
    client = steam / "steamapps" / "common" / "Path of Exile" / "logs" / "Client.txt"
    client.parent.mkdir(parents=True)
    client.write_text("", encoding="utf-8")

    monkeypatch.setattr(detector, "steam_library_roots", lambda: [steam])
    monkeypatch.setattr(detector, "launcher_candidates", lambda _version: [])

    assert detector.detect_client_log_paths() == {"poe1": str(client), "poe2": ""}


def test_detect_client_log_paths_uses_launcher_candidate_when_steam_is_absent(tmp_path, monkeypatch):
    client = tmp_path / "PathOfExile2" / "logs" / "Client.txt"
    client.parent.mkdir(parents=True)
    client.write_text("", encoding="utf-8")

    monkeypatch.setattr(detector, "steam_library_roots", lambda: [])
    monkeypatch.setattr(detector, "launcher_candidates", lambda version: [client] if version == "poe2" else [])

    assert detector.detect_client_log_paths() == {"poe1": "", "poe2": str(client)}


def test_detect_client_log_paths_uses_poe2_official_launcher_install(tmp_path, monkeypatch):
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path))
    client = tmp_path / "Grinding Gear Games" / "Path of Exile 2" / "logs" / "Client.txt"
    client.parent.mkdir(parents=True)
    client.write_text("", encoding="utf-8")
    monkeypatch.setattr(detector, "steam_library_roots", lambda: [])

    assert detector.detect_client_log_paths() == {"poe1": "", "poe2": str(client)}
