from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


def extract_relations(source: str) -> list[dict]:
    """AwakenedのPSEUDO_RULESからgroup/replaces付き定義を順序付きで抽出する。"""
    marker = "const PSEUDO_RULES"
    start = source.index(marker)
    start = source.index("[", start)
    end = source.index("\n]\n\nexport function filterPseudo", start)
    body = source[start + 1:end]
    blocks: list[str] = []
    depth = 0
    block_start: int | None = None
    quote: str | None = None
    escaped = False
    for index, char in enumerate(body):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char == "{":
            if depth == 0:
                block_start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and block_start is not None:
                blocks.append(body[block_start:index + 1])
                block_start = None

    relations = []
    for order, block in enumerate(blocks):
        pseudo = re.search(r"pseudo:\s*stat\('([^']+)'\)", block)
        group = re.search(r"\bgroup:\s*'([^']+)'", block)
        replaces = re.search(r"\breplaces:\s*'([^']+)'", block)
        if not pseudo or not (group or replaces):
            continue
        row = {"order": order, "pseudo_ref": pseudo.group(1)}
        if group:
            row["group"] = group.group(1)
        if replaces:
            row["replaces"] = replaces.group(1)
        relations.append(row)
    return relations


def pseudo_ids(stats_path: Path) -> dict[str, str]:
    result = {}
    for line in stats_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        candidates = row.get("stats", [row])
        for candidate in candidates:
            ids = candidate.get("trade", {}).get("ids", {}).get("pseudo", [])
            if ids:
                result[candidate["ref"]] = ids[0]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("stats", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    relations = extract_relations(raw.decode("utf-8"))
    ids = pseudo_ids(args.stats)
    for row in relations:
        row["stat_id"] = ids[row["pseudo_ref"]]
    payload = {
        "schema_version": 1,
        "source_revision": args.revision,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "relations": relations,
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
