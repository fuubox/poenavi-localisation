import json

from PySide6.QtWidgets import QApplication

from src.ui.settings_dialog import SettingsDialog


def test_alt_d_is_default_poetore_capture_hotkey():
    with open("default_config.json", encoding="utf-8") as file:
        config = json.load(file)
    assert config["hotkeys"]["poetore_capture"] == "alt+d"


def test_settings_dialog_can_change_poetore_capture_hotkey(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        "src.ui.settings_dialog.load_guide_data",
        lambda _version: {},
    )
    monkeypatch.setattr(
        "src.ui.settings_dialog.load_zone_master_data",
        lambda: {
            "zone_data_by_version": {"poe1": {}, "poe2": {}},
            "town_zones_by_version": {"poe1": [], "poe2": []},
        },
    )
    monkeypatch.setattr(
        SettingsDialog,
        "_rebuild_zone_tab",
        lambda self: None,
    )
    monkeypatch.setattr(
        "src.ui.settings_dialog.save_zone_master_data",
        lambda *_args, **_kwargs: None,
    )

    dialog = SettingsDialog(
        current_config={
            "hotkeys": {"poetore_capture": "Ctrl+Shift+P"},
            "poe_version": "poe1",
            "poe_version_mode": "ask",
        }
    )
    try:
        assert dialog.poetore_capture_btn.key_text == "Ctrl+Shift+P"
        dialog.poetore_capture_btn.key_text = "Alt+Q"
        assert dialog.get_settings()["hotkeys"]["poetore_capture"] == "Alt+Q"
    finally:
        dialog.close()
        app.processEvents()
