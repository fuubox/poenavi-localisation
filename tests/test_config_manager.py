import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.utils.config_manager import ConfigManager


def write_default_config(app_dir: Path, overrides=None):
    config = {
        "schemaVersion": ConfigManager.CURRENT_SCHEMA_VERSION,
        "hotkeys": {
            "start_stop": "F1",
            "reset": "F2",
            "lap": "F3",
            "undo_lap": "F4",
            "logout": "F5",
            "click_through": "F6",
            "hideout": "F11",
            "monastery": "F12",
            "search_string_test": "none",
        },
        "poe_version": "poe1",
        "poe_version_mode": "ask",
        "text_color": "#e9ffbd",
        "guide_detail_level": "beginner",
        "guide_detail_level_selected": False,
        "always_on_top": True,
        "notified_update_version": "",
    }
    if overrides:
        for key, value in overrides.items():
            if isinstance(config.get(key), dict) and isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
    (app_dir / ConfigManager.DEFAULT_CONFIG_FILE).write_text(
        json.dumps(config), encoding="utf-8"
    )
    return config


class ConfigManagerTest(unittest.TestCase):
    def test_save_and_load_uses_user_data_dir_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            write_default_config(app_dir)
            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                config = {"text_color": "#ffffff"}
                ConfigManager.save_config(config)

                config_path = user_dir / ConfigManager.CONFIG_FILE
                self.assertTrue(config_path.exists())
                self.assertEqual(ConfigManager.load_config()["text_color"], "#ffffff")
                self.assertEqual(ConfigManager.load_config()["schemaVersion"], ConfigManager.CURRENT_SCHEMA_VERSION)
                self.assertEqual(ConfigManager.load_config()["hotkeys"]["reset"], "F2")

    def test_legacy_config_is_migrated_to_user_data_dir_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            write_default_config(app_dir)
            legacy_config = {
                "hotkeys": {"start_stop": "F7"},
                "text_color": "#abcdef",
            }
            (app_dir / ConfigManager.CONFIG_FILE).write_text(
                json.dumps(legacy_config), encoding="utf-8"
            )

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                loaded = ConfigManager.load_config()

                self.assertEqual(loaded["hotkeys"]["start_stop"], "F7")
                self.assertEqual(loaded["hotkeys"]["reset"], "F2")
                self.assertEqual(loaded["text_color"], "#abcdef")
                self.assertEqual(loaded["guide_detail_level"], "beginner")
                self.assertFalse(loaded["guide_detail_level_selected"])
                self.assertTrue(loaded["always_on_top"])
                self.assertEqual(loaded["notified_update_version"], "")
                self.assertEqual(loaded["schemaVersion"], ConfigManager.CURRENT_SCHEMA_VERSION)
                self.assertTrue((user_dir / ConfigManager.CONFIG_FILE).exists())
                self.assertFalse((app_dir / ConfigManager.CONFIG_FILE).exists())
                self.assertEqual(len(list(user_dir.glob("config.backup-legacy-*.json"))), 1)

    def test_existing_user_config_wins_over_legacy_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            user_dir.mkdir()
            write_default_config(app_dir)
            (app_dir / ConfigManager.CONFIG_FILE).write_text(
                json.dumps({"text_color": "#legacy"}), encoding="utf-8"
            )
            (user_dir / ConfigManager.CONFIG_FILE).write_text(
                json.dumps({"text_color": "#user"}), encoding="utf-8"
            )

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                loaded = ConfigManager.load_config()

                self.assertEqual(loaded["text_color"], "#user")
                self.assertEqual(loaded["hotkeys"]["reset"], "F2")
                self.assertFalse((app_dir / ConfigManager.CONFIG_FILE).exists())
                self.assertEqual(len(list(user_dir.glob("config.backup-legacy-*.json"))), 0)
                self.assertEqual(len(list(user_dir.glob("config.backup-ignored-legacy-*.json"))), 1)

    def test_default_config_template_is_used_when_no_user_or_legacy_config_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            write_default_config(app_dir, {
                "hotkeys": {"start_stop": "F12"},
                "text_color": "#123456",
            })

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                loaded = ConfigManager.load_config()

                self.assertEqual(loaded["hotkeys"]["start_stop"], "F12")
                self.assertEqual(loaded["hotkeys"]["reset"], "F2")
                self.assertEqual(loaded["text_color"], "#123456")
                self.assertEqual(loaded["schemaVersion"], ConfigManager.CURRENT_SCHEMA_VERSION)
                self.assertTrue((user_dir / ConfigManager.CONFIG_FILE).exists())

    def test_legacy_config_wins_over_default_config_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            write_default_config(app_dir, {"text_color": "#default"})
            (app_dir / ConfigManager.CONFIG_FILE).write_text(
                json.dumps({"text_color": "#legacy"}), encoding="utf-8"
            )

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                loaded = ConfigManager.load_config()

                self.assertEqual(loaded["text_color"], "#legacy")
                self.assertFalse((app_dir / ConfigManager.CONFIG_FILE).exists())
                self.assertEqual(len(list(user_dir.glob("config.backup-legacy-*.json"))), 1)

    def test_load_config_migrates_startup_user_files_at_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            write_default_config(app_dir)
            legacy_files = {
                "notes_poe1.json": "[]",
                "notes_extra.json": "[\"extra\"]",
                "vendor_search_presets.json": "{\"presets\": []}",
                "progress_flags_poe2.json": "{\"active_flags\": []}",
                "timer_poe1.json": "{\"elapsed_ms\": 123}",
            }
            for filename, content in legacy_files.items():
                (app_dir / filename).write_text(content, encoding="utf-8")

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                ConfigManager.load_config()

                for filename, content in legacy_files.items():
                    self.assertEqual((user_dir / filename).read_text(encoding="utf-8"), content)
                    self.assertFalse((app_dir / filename).exists())

    def test_legacy_user_file_is_copied_to_user_data_dir_and_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            (app_dir / "notes_poe1.json").write_text("[]", encoding="utf-8")

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                migrated_path = ConfigManager.migrate_legacy_user_file("notes_poe1.json")

                self.assertEqual(migrated_path, (user_dir / "notes_poe1.json").resolve())
                self.assertEqual((user_dir / "notes_poe1.json").read_text(encoding="utf-8"), "[]")
                self.assertFalse((app_dir / "notes_poe1.json").exists())

    def test_existing_user_file_wins_and_legacy_user_file_is_backed_up_then_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()
            user_dir.mkdir()
            (app_dir / "notes_poe1.json").write_text("[\"legacy\"]", encoding="utf-8")
            (user_dir / "notes_poe1.json").write_text("[\"user\"]", encoding="utf-8")

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                migrated_path = ConfigManager.migrate_legacy_user_file("notes_poe1.json")

                self.assertEqual(migrated_path, (user_dir / "notes_poe1.json").resolve())
                self.assertEqual((user_dir / "notes_poe1.json").read_text(encoding="utf-8"), "[\"user\"]")
                self.assertFalse((app_dir / "notes_poe1.json").exists())
                backups = list(user_dir.glob("notes_poe1.backup-ignored-legacy-*.json"))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].read_text(encoding="utf-8"), "[\"legacy\"]")

    def test_missing_default_config_template_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            user_dir = Path(tmp) / "user-data"
            app_dir.mkdir()

            with patch.dict(os.environ, {ConfigManager.ENV_USER_DATA_DIR: str(user_dir)}), \
                 patch.object(ConfigManager, "get_app_dir", return_value=app_dir):
                with self.assertRaises(FileNotFoundError):
                    ConfigManager.load_config()


if __name__ == "__main__":
    unittest.main()
