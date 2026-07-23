from __future__ import annotations

from .parser import parse_item_text


def merge_normal_and_detailed_copy(normal_text: str, detailed_text: str) -> str:
    """詳細コピーのMod情報を保ち、表示名・ベース・レアリティを通常コピー側へ戻す。"""
    normal_item = parse_item_text(normal_text)
    detailed_item = parse_item_text(detailed_text)

    lines = detailed_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    separator_index = next((index for index, line in enumerate(lines) if line.strip() == "--------"), None)
    if separator_index is None:
        return detailed_text

    header = lines[:separator_index]
    # 詳細コピーはMagic品でもクラフト元のNormalベースとして返す場合がある。
    # 現物のレアリティは通常コピー側が正なので、ヘッダー行ごと引き継ぐ。
    normal_rarity_line = next((
        line for line in normal_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if line.startswith("Rarity:") or line.startswith("レアリティ:")
    ), None)
    if normal_rarity_line:
        for index, line in enumerate(header):
            if line.startswith("Rarity:") or line.startswith("レアリティ:"):
                header[index] = normal_rarity_line
                break
    for old, new in (
        (detailed_item.name, normal_item.name),
        (detailed_item.base_type, normal_item.base_type),
    ):
        if not old or not new:
            continue
        for index in range(2, len(header)):
            if header[index].strip() == old.strip():
                header[index] = new
                break

    return "\n".join(header + lines[separator_index:])
