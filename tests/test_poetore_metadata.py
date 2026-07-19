import json

from src.poetore.metadata import MetadataIndex, ModMetadata
from src.poetore.metadata_builder import build_minimal_index


def test_builder_joins_awakened_and_japanese_by_trade_id_and_keeps_minimal_fields():
    awakened = [json.dumps({
        "ref": "+# to maximum Life", "better": 1,
        "matchers": [{"string": "+# to maximum Life"}],
        "trade": {"ids": {"explicit": ["explicit.stat_life"]}},
    })]
    jp = {"result": [{"entries": [{
        "id": "explicit.stat_life", "type": "explicit", "text": "最大ライフ +#",
    }]}]}
    repoe_stats = {"base_maximum_life": {"is_local": False}}
    repoe_mods = {"Life1": {
        "domain": "item", "text": "+(10-19) to maximum Life", "required_level": 1,
        "generation_type": "prefix", "stats": [{"id": "base_maximum_life", "min": 10, "max": 19}],
    }}
    payload = build_minimal_index(awakened, jp, repoe_stats, repoe_mods)
    row = payload["mods"][0]
    assert row["stat_id"] == "explicit.stat_life"
    assert row["japanese"] == ["最大ライフ +#"]
    assert set(row) == {"ref", "stat_id", "kind", "japanese", "better", "inverted", "exact", "local", "tiers"}


def test_metadata_search_bounds_support_minimum_maximum_and_exact():
    assert ModMetadata("r", "id", "explicit", ("被ダメージが#%増加する",), better=-1).search_bounds(20) == (None, 22.0)
    assert ModMetadata("r", "id", "explicit", ("値 #",), better=0).search_bounds(3) == (3, 3)
    assert ModMetadata("r", "id", "explicit", ("値 #",), better=1).search_bounds(100, 90, 100) == (100.0, None)


def test_metadata_index_matches_normalized_japanese_detail_copy():
    index = MetadataIndex((ModMetadata(
        "+# to maximum Life", "explicit.life", "explicit", ("最大ライフ +#",),
    ),))
    record, confidence = index.match("最大ライフ +100(90-100)", "prefix")
    assert record and record.stat_id == "explicit.life"
    assert confidence == 1.0
