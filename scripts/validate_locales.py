"""Read-only release validation for PoENavi locale resources."""

from __future__ import annotations

import ast
import collections
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TRANSLATABLE_GUIDE_FIELDS = {"objective", "layout", "tips", "summary", "text"}
ALLOWED_TAG = re.compile(r"^</?span(?:\s+style\s*=\s*['\"]\s*color\s*:\s*#[0-9a-fA-F]{3,8}\s*;?\s*['\"])?\s*>$")
TOKEN_RE = re.compile(r"\[(?:quest|boss|town|move|logout|note|star|trial|craft|wp|portal)\]")
TAG_RE = re.compile(r"</?[^>]+>")
UI_LITERAL_CONSTRUCTORS = {"QLabel", "QPushButton", "QCheckBox", "QGroupBox", "QRadioButton"}
UI_LITERAL_METHODS = {
    "setText",
    "setWindowTitle",
    "setToolTip",
    "setPlaceholderText",
    "addItem",
    "addTab",
    "addAction",
    "addButton",
}
MESSAGE_BOX_METHODS = {"information", "question", "warning", "critical"}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _flatten_strings(value: Any, prefix: str = "") -> dict[str, str]:
    result: dict[str, str] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            result.update(_flatten_strings(child, child_prefix))
    elif isinstance(value, str):
        result[prefix] = value
    return result


def _placeholders(value: str) -> set[str]:
    return {
        match.group(1).split(".", 1)[0].split("[", 1)[0]
        for match in re.finditer(r"\{([A-Za-z_][A-Za-z0-9_.\[\]]*)[^}]*\}", value)
    }


def validate_catalogs(root: Path = ROOT) -> list[str]:
    ja = _flatten_strings(_load_json(root / "data" / "i18n" / "ja.json"))
    en = _flatten_strings(_load_json(root / "data" / "i18n" / "en.json"))
    errors: list[str] = []
    if set(ja) != set(en):
        errors.append(f"catalog key sets differ: ja-only={sorted(set(ja)-set(en))}, en-only={sorted(set(en)-set(ja))}")
    for key in sorted(set(ja) & set(en)):
        if _placeholders(ja[key]) != _placeholders(en[key]):
            errors.append(f"placeholder mismatch for catalog key {key}")
    return errors


def _guide_walk(value: Any, path: str = "") -> Iterable[tuple[str, str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}/{key}"
            if key in TRANSLATABLE_GUIDE_FIELDS and isinstance(child, str):
                yield child_path, key, child
            else:
                yield from _guide_walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _guide_walk(child, f"{path}/{index}")


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_shape(child) for child in value]
    return type(value).__name__


def _protected_values(value: Any, path: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            child_path = f"{path}/{key}"
            if key in TRANSLATABLE_GUIDE_FIELDS:
                continue
            result.update(_protected_values(child, child_path))
        return result
    if isinstance(value, list):
        result: dict[str, Any] = {}
        for index, child in enumerate(value):
            result.update(_protected_values(child, f"{path}/{index}"))
        return result
    return {path: value}


def _tags(value: str) -> list[str]:
    return TAG_RE.findall(value)


def validate_guides(root: Path = ROOT) -> list[str]:
    pairs = (
        ("guide_data.json", "guide_data_en.json"),
        ("guide_data_poe2.json", "guide_data_poe2_en.json"),
    )
    errors: list[str] = []
    for ja_name, en_name in pairs:
        ja = _load_json(root / ja_name)
        en = _load_json(root / en_name)
        if _shape(ja) != _shape(en):
            errors.append(f"guide structure differs: {ja_name} / {en_name}")
        if _protected_values(ja) != _protected_values(en):
            errors.append(f"protected guide values differ: {ja_name} / {en_name}")
        for path, field, ja_value in _guide_walk(ja):
            matching = {item_path: item_value for item_path, _item_field, item_value in _guide_walk(en)}.get(path, "")
            if ja_value and not matching:
                errors.append(f"empty English guide leaf: {en_name}{path}")
            if _contains_japanese(matching):
                errors.append(f"Japanese text remains in English guide leaf: {en_name}{path}")
            if collections.Counter(TOKEN_RE.findall(ja_value)) != collections.Counter(TOKEN_RE.findall(matching)):
                errors.append(f"mini-navi token mismatch: {en_name}{path}")
            for tag in _tags(matching):
                if not ALLOWED_TAG.match(tag):
                    errors.append(f"unsupported guide markup {tag!r}: {en_name}{path}")
            if len(ja_value.splitlines()) != len(matching.splitlines()):
                errors.append(f"guide line count changed: {en_name}{path}")
    return errors


def validate_zone_english(root: Path = ROOT) -> list[str]:
    data = _load_json(root / "data" / "zone_data.json")
    errors: list[str] = []
    versions = data.get("zone_data_by_version", data)
    for version, acts in versions.items():
        if not isinstance(acts, dict):
            continue
        for act, zones in acts.items():
            for zone in zones:
                if not zone.get("zone_en"):
                    errors.append(f"missing zone_en: {version}/{act}/{zone.get('id')}")
    return errors


def _static_tr_keys(root: Path) -> tuple[set[str], list[str]]:
    keys: set[str] = set()
    errors: list[str] = []
    source_roots = [root / "main.py", root / "updater_main.py", root / "src"]
    paths = [path for base in source_roots if base.is_file() for path in [base]]
    paths += [path for base in source_roots if base.is_dir() for path in base.rglob("*.py")]
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "tr":
                if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                    errors.append(f"non-literal tr key: {path}:{node.lineno}")
                else:
                    keys.add(node.args[0].value)
    return keys, errors


def validate_static_translation_keys(root: Path = ROOT) -> list[str]:
    keys, errors = _static_tr_keys(root)
    catalog = _flatten_strings(_load_json(root / "data" / "i18n" / "ja.json"))
    errors.extend(f"unknown translation key {key!r}" for key in sorted(keys) if key not in catalog)
    return errors


def _contains_japanese(value: str) -> bool:
    return any(
        ("\u3040" <= character <= "\u30ff")
        or ("\u3400" <= character <= "\u9fff")
        for character in value
    )


def _literal_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str))
    return None


def validate_raw_ui_literals(root: Path = ROOT) -> list[str]:
    """Ensure user-facing Japanese literals are explicitly passed through ui_text.

    The language picker is intentionally bilingual and is the sole UI exemption.
    Domain data and comments are outside this check; only arguments to common
    Qt display APIs are inspected.
    """
    errors: list[str] = []
    for path in (root / "src" / "ui").rglob("*.py"):
        if path.name == "language_dialog.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            argument_indexes: tuple[int, ...] = ()
            if isinstance(node.func, ast.Name) and node.func.id in UI_LITERAL_CONSTRUCTORS:
                argument_indexes = (0,)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in UI_LITERAL_METHODS:
                argument_indexes = (0, 1) if node.func.attr in {"addTab", "addButton"} else (0,)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in MESSAGE_BOX_METHODS:
                argument_indexes = (1, 2)
            for index in argument_indexes:
                if index >= len(node.args):
                    continue
                value = _literal_text(node.args[index])
                if value is not None and _contains_japanese(value):
                    errors.append(f"raw Japanese UI literal: {path}:{node.lineno}")
    return errors


def validate_resources(root: Path = ROOT) -> list[str]:
    build_script = (root / "scripts" / "build_release.ps1").read_text(encoding="utf-8")
    required = (
        "data\\i18n",
        "guide_data.json",
        "guide_data_poe2.json",
        "guide_data_en.json",
        "guide_data_poe2_en.json",
    )
    return [f"packaging script does not register {name}" for name in required if name not in build_script]


def validate_all(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for validator in (
        validate_catalogs,
        validate_guides,
        validate_zone_english,
        validate_static_translation_keys,
        validate_raw_ui_literals,
        validate_resources,
    ):
        try:
            errors.extend(validator(root))
        except Exception as exc:
            errors.append(f"{validator.__name__} failed: {exc}")
    return errors


if __name__ == "__main__":
    failures = validate_all()
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        raise SystemExit(1)
    print("Locale validation passed: ja/en catalogs, English guides, zone names, static keys, UI literals, and resources are valid.")
