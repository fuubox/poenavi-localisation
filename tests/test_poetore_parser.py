import unittest

from src.poetore import ItemParseError, parse_item_text


RARE_JP = """アイテムクラス: 指輪
レアリティ: レア
嵐の 輪
アメジストの指輪
--------
装備条件:
レベル: 60
--------
アイテムレベル: 84
--------
+23% 混沌耐性 (implicit)
--------
+72 最大ライフ
+35% 火耐性
未鑑定
"""


class PoetoreParserTest(unittest.TestCase):
    def test_parses_japanese_rare_item_into_public_model(self):
        item = parse_item_text(RARE_JP)
        self.assertEqual(item.item_class, "指輪")
        self.assertEqual(item.rarity, "レア")
        self.assertEqual(item.name, "嵐の 輪")
        self.assertEqual(item.base_type, "アメジストの指輪")
        self.assertEqual(item.category, "accessory")
        self.assertEqual(item.item_level, 84)
        self.assertEqual(item.flags, ("unidentified",))
        self.assertEqual(len(item.modifiers), 3)
        self.assertEqual(item.modifiers[0].kind, "implicit")
        self.assertEqual(item.modifiers[0].values, (23.0,))

    def test_parses_english_normal_item_and_crlf(self):
        item = parse_item_text(
            "Item Class: Currency\r\nRarity: Normal\r\nChaos Orb\r\n--------\r\nStack Size: 4/20\r\n"
        )
        self.assertEqual(item.name, "Chaos Orb")
        self.assertEqual(item.base_type, "Chaos Orb")
        self.assertEqual(item.category, "currency")
        self.assertEqual(item.properties["Stack Size"], "4/20")

    def test_rejects_non_item_text(self):
        with self.assertRaises(ItemParseError):
            parse_item_text("ただの文章です")

    def test_weapon_properties_and_requirements_are_not_modifiers(self):
        item = parse_item_text("""Item Class: Bows
Rarity: Rare
Storm Reach
Spine Bow
--------
Bow
Physical Damage: 38-115 (augmented)
Critical Strike Chance: 6.50%
Attacks per Second: 1.50
--------
Requirements:
Level: 64
Dexterity: 212
--------
Sockets: G-G-G-G-G-G
--------
Item Level: 84
--------
+24% to Global Critical Strike Multiplier (implicit)
--------
{ Prefix Modifier "Vicious" (Tier: 3) }
120% increased Physical Damage
{ Suffix Modifier "of the Lynx" (Tier: 2) }
+31 to Dexterity
""")
        self.assertEqual(len(item.modifiers), 3)
        self.assertEqual([mod.kind for mod in item.modifiers], ["implicit", "prefix", "suffix"])
        self.assertIn("Physical Damage", item.properties)
        self.assertIn("Requirements", item.properties)
        self.assertNotIn("Bow", [mod.text for mod in item.modifiers])

    def test_modifier_header_is_not_counted_as_a_modifier(self):
        item = parse_item_text("""Item Class: Rings
Rarity: Rare
Coil Band
Gold Ring
--------
Requirements:
Level: 40
--------
Item Level: 70
--------
{ Crafted Prefix Modifier }
+45 to maximum Life (crafted)
""")
        self.assertEqual(len(item.modifiers), 1)
        self.assertEqual(item.modifiers[0].kind, "crafted")


if __name__ == "__main__":
    unittest.main()
