from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Iterable

from .metadata import normalize_stat_text


SUPPORTED_KINDS = {"explicit", "implicit", "crafted", "fractured", "enchant"}


def _awakened_stats(lines: Iterable[str]) -> list[dict]:
    rows = []
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        rows.extend(row.get("stats", ())) if "stats" in row else rows.append(row)
    return rows


def _trade_entries(payload: dict) -> dict[tuple[str, str], dict]:
    return {
        (str(entry.get("type", "")), str(entry.get("id", ""))): entry
        for group in payload.get("result", ()) for entry in group.get("entries", ())
    }


def _repoe_by_ref(stats: dict, mods: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for mod_id, mod in mods.items():
        if mod.get("domain") != "item" or not mod.get("stats"):
            continue
        ref = normalize_stat_text(str(mod.get("text", "")))
        if not ref:
            continue
        local = any(bool(stats.get(stat.get("id"), {}).get("is_local")) for stat in mod["stats"])
        tier_rows = result.setdefault(ref, {"local": False, "tiers": []})
        tier_rows["local"] = tier_rows["local"] or local
        first = mod["stats"][0]
        tier_rows["tiers"].append({
            "tier": None,
            "minimum": float(first.get("min", 0)),
            "maximum": float(first.get("max", 0)),
            "required_level": int(mod.get("required_level", 0)) or None,
            "generation": mod.get("generation_type"),
            "mod_id": mod_id,
        })
    return result


def build_minimal_index(awakened_lines: Iterable[str], jp_trade: dict,
                        repoe_stats: dict | None = None,
                        repoe_mods: dict | None = None,
                        sources: dict | None = None) -> dict:
    """必要な照合・検索項目だけに縮小した派生インデックスを生成する。"""
    jp = _trade_entries(jp_trade)
    repoe = _repoe_by_ref(repoe_stats or {}, repoe_mods or {})
    records = []
    seen = set()
    for stat in _awakened_stats(awakened_lines):
        trade = stat.get("trade") or {}
        for kind, ids in (trade.get("ids") or {}).items():
            if kind not in SUPPORTED_KINDS:
                continue
            for stat_id in ids:
                entry = jp.get((kind, stat_id))
                if not entry or (kind, stat_id) in seen:
                    continue
                seen.add((kind, stat_id))
                repoe_row = repoe.get(normalize_stat_text(str(stat.get("ref", ""))), {})
                records.append({
                    "ref": str(stat.get("ref", "")),
                    "stat_id": stat_id,
                    "kind": kind,
                    "japanese": [str(entry.get("text", ""))],
                    "better": int(stat.get("better", 1)),
                    "inverted": bool(trade.get("inverted", False)),
                    "exact": int(stat.get("better", 1)) == 0 or bool(trade.get("option", False)),
                    "local": bool(repoe_row.get("local", False)),
                    "tiers": repoe_row.get("tiers", ()),
                })
    records.sort(key=lambda row: (row["kind"], row["stat_id"]))
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources or {},
        "scope": "PoE1 trade stat matching for weapons, armour and accessories",
        "mods": records,
    }
