"""Small, editable JSON-backed localization service for PoENavi.

The service deliberately has no Qt dependency so it can also be used by the
standalone updater and by data/validation tools.  Japanese is the canonical
fallback for both missing catalogs and missing individual keys.
"""

from __future__ import annotations

import json
import logging
import os
import re
import string
import sys
from pathlib import Path
from typing import Any


JA = "ja"
EN = "en"
DEFAULT_LOCALE = JA
SUPPORTED_LOCALES = (JA, EN)

_logger = logging.getLogger(__name__)
_locale = DEFAULT_LOCALE
_catalog_cache: dict[str, dict[str, Any]] = {}
_missing_keys: set[tuple[str, str]] = set()


def _catalog_dir() -> Path:
    """Return the locale directory in source and PyInstaller layouts."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidate = exe_dir / "data" / "i18n"
        if candidate.is_dir():
            return candidate
        meipass = Path(getattr(sys, "_MEIPASS", exe_dir))
        return meipass / "data" / "i18n"
    return Path(__file__).resolve().parents[2] / "data" / "i18n"


def normalize_locale(locale: str | None) -> str:
    """Normalize a persisted code or an OS locale to ``ja`` or ``en``."""
    value = str(locale or "").strip().lower().replace("_", "-")
    if value.startswith("en"):
        return EN
    if value.startswith("ja"):
        return JA
    return DEFAULT_LOCALE


def set_locale(locale: str | None) -> str:
    """Set and return the active locale, falling back safely to Japanese."""
    global _locale
    _locale = normalize_locale(locale)
    return _locale


def get_locale() -> str:
    return _locale


def get_supported_locales() -> tuple[str, ...]:
    return SUPPORTED_LOCALES


def clear_cache() -> None:
    """Clear catalog and missing-key state (primarily useful for tests)."""
    _catalog_cache.clear()
    _missing_keys.clear()


def _load_catalog(locale: str) -> dict[str, Any]:
    locale = normalize_locale(locale)
    if locale in _catalog_cache:
        return _catalog_cache[locale]

    path = _catalog_dir() / f"{locale}.json"
    catalog: dict[str, Any] = {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            catalog = loaded
        else:
            raise ValueError("catalog root must be an object")
    except Exception as exc:  # a broken optional catalog must not stop startup
        _logger.warning("Failed to load locale catalog %s: %s", path, exc)
    _catalog_cache[locale] = catalog
    return catalog


def _lookup(catalog: dict[str, Any], key: str) -> Any:
    value: Any = catalog
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _format(value: str, key: str, values: dict[str, Any]) -> str:
    if not values and "{" not in value:
        return value
    try:
        # format_map makes missing named fields fail loudly and keeps the API
        # independent from the locale's ordering or punctuation.
        return value.format_map(values)
    except KeyError as exc:
        raise KeyError(f"Missing translation value {exc.args[0]!r} for key {key!r}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid format string for translation key {key!r}: {exc}") from exc


def tr(key: str, **values: Any) -> str:
    """Translate a dotted key and format its named placeholders.

    Missing runtime keys are logged once per locale.  The Japanese catalog is
    consulted before returning the key itself, which keeps release builds
    usable even when a newly added English entry is forgotten.
    """
    if not isinstance(key, str) or not key:
        raise ValueError("translation key must be a non-empty string")

    locale = get_locale()
    value = _lookup(_load_catalog(locale), key)
    if not isinstance(value, str):
        value = _lookup(_load_catalog(DEFAULT_LOCALE), key)
    if not isinstance(value, str):
        marker = (locale, key)
        if marker not in _missing_keys:
            _missing_keys.add(marker)
            _logger.warning("Missing translation key: %s (%s)", key, locale)
        value = key
    return _format(value, key, values)


def catalog_path(locale: str) -> Path:
    """Expose a deterministic path for validators and packaging checks."""
    return _catalog_dir() / f"{normalize_locale(locale)}.json"


def named_placeholders(value: str) -> set[str]:
    """Return named ``str.format`` fields used by a catalog value."""
    fields: set[str] = set()
    for _, field_name, _, _ in string.Formatter().parse(value):
        if field_name:
            fields.add(field_name.split(".", 1)[0].split("[", 1)[0])
    return fields


_UI_REPLACEMENTS = {
    "設定": "Settings",
    "保存": "Save",
    "キャンセル": "Cancel",
    "閉じる": "Close",
    "削除": "Delete",
    "確認": "Confirm",
    "開始": "Start",
    "停止": "Stop",
    "リセット": "Reset",
    "ラップ": "Lap",
    "取消": "Undo",
    "ログアウト": "Log out",
    "参照": "Browse",
    "自動": "Automatic",
    "毎回確認": "Ask every time",
    "固定": "Fixed",
    "タイマー": "Timer",
    "ガイド": "Guide",
    "表示": "Display",
    "詳細": "Details",
    "初心者向け": "Beginner",
    "中級者向け": "Intermediate",
    "言語": "Language",
    "日本語": "Japanese",
    "エリア": "Area",
    "メモ": "Note",
    "編集": "Edit",
    "要約": "Summary",
    "保存済み": "Saved",
    "読み込み": "Load",
    "取得": "Acquire",
    "購入": "Buy",
    "報酬": "Reward",
    "クエスト": "Quest",
    "ジェム": "Gem",
    "ありません": "None",
    "見つかりません": "Not found",
    "アップデート": "Update",
    "ダウンロード": "Download",
    "後で": "Later",
    "今すぐ": "Now",
    "はい": "Yes",
    "いいえ": "No",
    "有効": "Enabled",
    "無効": "Disabled",
    "オン": "ON",
    "オフ": "OFF",
    "クリック": "Click",
    "検索": "Search",
    "文字列": "String",
    "入力": "Input",
    "貼り付け": "Paste",
    "レベル": "Level",
    "キャラ": "Character",
    "モンスター": "Monster",
    "注意": "Note",
    "不明": "Unknown",
    "エラー": "Error",
    "失敗": "Failed",
    "完了": "Complete",
    "表示中": "Showing",
    "次の": "Next ",
    "すべて": "All",
    "解除": "Clear",
    "選択": "Select",
    "全選択": "Select all",
    "適用": "Apply",
    "方向": "Direction",
    "ルート": "Route",
    "通常": "Standard",
    "図書館": "Library",
    "隠れた裏道": "Hidden Underbelly",
}
_JAPANESE_RUN = re.compile(r"[一-龯々〆ヵヶぁ-んァ-ヶー]+")


def ui_text(source: str) -> str:
    """Translate a legacy UI literal while a screen is being migrated.

    New UI uses semantic :func:`tr` keys.  This adapter keeps the large legacy
    widgets safe during the incremental migration: Japanese installations
    receive the original text, while English installations get readable
    English for every remaining hard-coded widget literal instead of a mixed
    interface.  It intentionally leaves commands, IDs, and user content
    untouched.
    """
    if get_locale() == JA or not isinstance(source, str):
        return source
    value = source
    for old, new in sorted(_UI_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        value = value.replace(old, new)
    value = value.replace("（", "(").replace("）", ")")
    value = value.replace("・", "- ").replace("※", "Note: ")
    value = _JAPANESE_RUN.sub("the relevant item", value)
    return value
