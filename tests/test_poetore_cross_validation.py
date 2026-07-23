import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.poetore.parser import parse_item_text
from src.poetore.trade import build_search_query, resolve_trade_stat_filters


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "poetore" / "step10_cases.json"


def _cases():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["id"])
def test_step10_item_matrix_produces_expected_search_query(case):
    item = parse_item_text(case["text"])
    entries = tuple(case.get("stat_entries", ()))
    with patch("src.poetore.trade._trade_stat_entries", return_value=entries):
        filters = resolve_trade_stat_filters(item)

    enabled = {row.stat_id: row.min_value for row in filters if row.enabled}
    assert enabled.keys() == case["expected_enabled"].keys()
    for stat_id, expected in case["expected_enabled"].items():
        assert enabled[stat_id] == pytest.approx(expected, abs=0.05)

    visible = {row.stat_id for row in filters}
    assert visible.issuperset(case.get("expected_visible", ()))

    query = build_search_query(
        item,
        case["trade_base"],
        filters,
        trade_name=case.get("trade_name"),
    )["query"]
    misc = query.get("filters", {}).get("misc_filters", {}).get("filters", {})
    for name, option in case.get("expected_misc", {}).items():
        assert misc[name] == {"option": option}
    for name in case.get("expected_absent_misc", ()):
        assert name not in misc
    if "expected_rarity" in case:
        rarity = query["filters"]["type_filters"]["filters"]["rarity"]
        assert rarity == {"option": case["expected_rarity"]}


def test_step10_fixture_ids_and_groups_are_unique_and_complete():
    cases = _cases()
    assert len(cases) >= 12
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(case["group"] and case["trade_base"] for case in cases)
