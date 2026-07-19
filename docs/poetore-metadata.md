# ぽえとれ Modメタデータ基盤

## 目的と境界

PoE 1の武器・防具・装飾品について、日本語コピー文を共通Mod定義とTrade API stat IDへ
対応付ける。アプリにはRePoEの全データを同梱せず、検索に必要な項目だけへ変換した
`data/poetore/mod_metadata.json`を同梱する。

## 情報源

- Awakened PoE Trade: 共通ref、数値の良し悪し、Trade API ID、反転・完全一致ルール
- RePoE: Tier範囲、必要レベル、Prefix/Suffix等の生成種別、ローカルstat判定
- 日本語公式Trade API: 日本語matcherとTrade API stat ID

生成物には各取得元URLと取得内容のSHA-256を記録する。更新は次のコマンドで明示的に行い、
差分とテストを確認してからコミットする。

```bash
PYTHONPATH=. python3 scripts/build_poetore_metadata.py
```

## 独自スキーマ

- 共通Mod: `ref`, `stat_id`, `kind`, `better`, `inverted`, `exact`, `local`
- 日本語matcher: `japanese`
- Tier: `tier`, `minimum`, `maximum`, `required_level`, `generation`, `mod_id`
- 実アイテム解析: `stat_id`, `ref`, `confidence`, `roll_min/max`, `better`, `inverted`

一致が一意なら確度1.0、同一日本語表記に複数候補があれば0.75、未解決は0.0とする。
未解決値を正本へ推測で書かず、従来の公式Trade API照合へフォールバックする。

## 数値検索

- `better=1`: 最小値を使用
- `better=-1`: 最大値を使用
- `better=0`または`exact=true`: 最小値と最大値を同値にする
- `inverted=true`: Trade API送信時に符号反転し、min/maxを入れ替える
- 通常レア: 実数値を既定割合で緩和
- ユニーク: 可変幅を基準に緩和し、完璧ロールは緩和しない

## 配布ルール

- RePoEの元JSONを配布物へ丸ごと含めない。
- ぽえとれに必要な最小フィールドだけを派生インデックスへ保存する。
- 無料・非公式ツールとして提供し、`THIRD_PARTY_NOTICES.md`の表示を維持する。
- 一般公開前に生成物の内容・サイズ・権利表記を再監査する。
