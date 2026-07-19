from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from src.poetore.metadata_builder import build_minimal_index


AWAKENED_STATS = "https://raw.githubusercontent.com/SnosMe/awakened-poe-trade/master/renderer/public/data/en/stats.ndjson"
JP_TRADE_STATS = "https://jp.pathofexile.com/api/trade/data/stats"
REPOE_STATS = "https://repoe-fork.github.io/stats.min.json"
REPOE_MODS = "https://repoe-fork.github.io/mods.min.json"


def _get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "PoENavi/poetore-metadata-builder"})
    with urlopen(request, timeout=120) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="ぽえとれ用の最小Modメタデータを生成")
    parser.add_argument("--output", type=Path, default=Path("data/poetore/mod_metadata.json"))
    args = parser.parse_args()
    blobs = {name: _get(url) for name, url in {
        "awakened_poe_trade": AWAKENED_STATS, "jp_trade_api": JP_TRADE_STATS,
        "repoe_stats": REPOE_STATS, "repoe_mods": REPOE_MODS,
    }.items()}
    awakened = blobs["awakened_poe_trade"].decode("utf-8").splitlines()
    jp_trade = json.loads(blobs["jp_trade_api"])
    repoe_stats = json.loads(blobs["repoe_stats"])
    repoe_mods = json.loads(blobs["repoe_mods"])
    payload = build_minimal_index(
        awakened, jp_trade, repoe_stats, repoe_mods,
        sources={name: {
            "url": url,
            "sha256": hashlib.sha256(blobs[name]).hexdigest(),
        } for name, url in {
            "awakened_poe_trade": AWAKENED_STATS, "jp_trade_api": JP_TRADE_STATS,
            "repoe_stats": REPOE_STATS, "repoe_mods": REPOE_MODS,
        }.items()},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"generated {len(payload['mods'])} records: {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
