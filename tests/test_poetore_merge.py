from src.poetore.merge import merge_normal_and_detailed_copy
from src.poetore.parser import parse_item_text


def test_uses_japanese_name_and_base_with_detailed_mods():
    normal = """アイテムクラス: 両手剣
レアリティ: レア
地獄の破滅
略奪者の剣
--------
アイテムレベル: 67
--------
物理ダメージが74%増加する
"""
    detailed = """Item Class: Two Hand Swords
Rarity: Rare
Pandemonium Bane
Reaver Sword
--------
Item Level: 67
--------
{ Prefix Modifier \"Vicious\" (Tier: 3) }
74% increased Physical Damage
"""

    merged = merge_normal_and_detailed_copy(normal, detailed)
    item = parse_item_text(merged)

    assert item.name == "地獄の破滅"
    assert item.base_type == "略奪者の剣"
    assert "{ Prefix Modifier" in merged
    assert "74% increased Physical Damage" in merged


def test_magic_single_line_name_keeps_display_name_while_detail_can_resolve_base():
    normal = """アイテムクラス: ワンド
レアリティ: マジック
酩薬の 痛憤の 浸潤のワンド
--------
アイテムレベル: 84
"""
    detailed = """Item Class: Wands
Rarity: Magic
Dissolution Imbued Wand of Torment
--------
Item Level: 84
"""
    merged = merge_normal_and_detailed_copy(normal, detailed)
    item = parse_item_text(merged)
    detailed_item = parse_item_text(detailed)
    assert item.name == item.base_type == "酩薬の 痛憤の 浸潤のワンド"
    assert detailed_item.name == detailed_item.base_type == "Dissolution Imbued Wand of Torment"
