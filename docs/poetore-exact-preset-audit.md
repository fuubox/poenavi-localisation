# Awakened専用Exactプリセット準拠監査

比較対象: Awakened PoE Trade `fa31bfbbe99e04e386b4af2d71d633e2b6823c0f`

## 準拠対象

- Gem: 名称/Variant、level、quality、corrupted、imbued候補
- Captured Beast: ビースト名の完全一致
- Map/Invitation: 名前またはbase、tier、Blighted、completion reward、Map専用stat
- Heist Contract/Blueprint: base、area level、job、target、revealed wings、Enchant除外
- Expedition Logbook: base、area level帯、Logbook専用stat
- Flask/Tincture: base、quality、T1/T2、crafted Flask Mod、Enchant/hybrid規則
- Memory Line/Sanctum Relic/Charm: 専用statをすべて初期選択
- Idol: Explicit候補と66%以上のroll初期選択
- Chronicle of Atzoatl/Mirrored Tablet/Forbidden Tome: area levelと専用Mod規則
- Normal/Unidentified: 完成品/ベース二択を出さず、Exact用条件だけを使用

共通規則もAwakenedへ揃える。

- Normal/Magic/Rareはrarity完全一致ではなく`nonunique`
- Magic Jewel/Abyss JewelのAdorned用途だけ`magic`完全一致
- Exactではpseudo、fractured、enchant、対象implicit、特殊生成Modを保持
- Magic Explicitは対象カテゴリだけ表示し、T1/T2を初期ON
- Rareの通常ExplicitはIdolを除いてExactから外す
- Exactのitem levelはカテゴリ別除外、上限86、Cluster帯、Flask/Tincture初期OFFを適用
- InfluenceはExactで初期ON
- Blighted Mapではrolled Map Modを出さず、Map本体条件だけを使う
- Forbidden Tomeがarea level 83未満なら同じlevelへ上下限を固定する

## 意図的な対象外

- Currency/Divination Cardの旧Bulk Exchange（通常の名前検索は維持）
- Metamorph Sample
- Sentinel
- Voidstone
- Charged Compass

これらはAwakenedとの差分として残すのではなく、ぽえとれの製品スコープ外とする。
