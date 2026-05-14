"""
攻略ガイドデータ管理
ゾーンIDをキーに、攻略テキスト（HTML対応）を返す。
データは PoEバージョンごとの guide_data*.json から読み込み。ユーザー編集可能。
"""

import html
import json
import os
import re
import sys

from src.utils.poe_version_data import POE1, get_guide_filename

# デフォルトガイド（guide_data.json がない場合のフォールバック）
DEFAULT_GUIDE = {
    "act1_area1": {
        "tips": "・左クリックに移動を割り当て、押しやすいボタンに攻撃スキルをセット"
    },
    "act1_area2": {
        "objective": "ウェイポイント（WP）を確保し、先へ進む",
        "layout": "【レイアウト情報】\n・入口の向きが右下なら、上に進む\n・入口の向きが左下を向いてるなら、下か右下（→右）に進む",
        "tips": "・ここの敵は経験値も大して美味しくないので、スルー推奨"
    },
}

def get_guide_dir():
    """ガイドデータファイルのディレクトリ（exeフォルダ優先 → _MEIPASS）"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return getattr(sys, '_MEIPASS', exe_dir) if not os.path.exists(exe_dir) else exe_dir
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_guide_path(poe_version: str = POE1) -> str:
    guide_file = get_guide_filename(poe_version)
    guide_dir = get_guide_dir()

    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        exe_path = os.path.join(exe_dir, guide_file)
        if os.path.exists(exe_path):
            return exe_path
        return os.path.join(getattr(sys, '_MEIPASS', exe_dir), guide_file)

    return os.path.join(guide_dir, guide_file)


def load_guide_data(poe_version: str = POE1) -> dict:
    """ガイドデータを読み込み"""
    path = get_guide_path(poe_version)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[GuideData] Failed to load ({poe_version}): {e}")
    return DEFAULT_GUIDE if poe_version == POE1 else {}


def save_guide_data(data: dict, poe_version: str = POE1):
    """ガイドデータを保存"""
    path = get_guide_path(poe_version)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[GuideData] Saved ({poe_version}): {path}")
    except Exception as e:
        print(f"[GuideData] Failed to save ({poe_version}): {e}")


def _get_route_for_zone(zone_id: str, config: dict | None) -> str:
    """zone_idからAct判定してルート設定を取得。"standard"なら空文字を返す"""
    if not config or not zone_id:
        return ""
    if zone_id.startswith("act3_"):
        route = config.get("poe1_route_act3", "standard")
    elif zone_id.startswith("act8_"):
        route = config.get("poe1_route_act8", "standard")
    else:
        return ""
    return "" if route == "standard" else route


def _resolve_structured_flag_guide(entry: dict, active_flags: set[str] | None) -> dict | None:
    if not isinstance(entry, dict):
        return None
    default_guide = entry.get("default")
    flags = entry.get("flags", {})
    if active_flags and isinstance(flags, dict):
        # 複数フラグ条件（例: act1_draven_dead+act1_asinia_dead）を優先
        composite_keys = [k for k in flags.keys() if "+" in k]
        composite_keys.sort(key=lambda k: len(k.split("+")), reverse=True)
        for flag_key in composite_keys:
            required = [part.strip() for part in flag_key.split("+") if part.strip()]
            if required and all(r in active_flags for r in required):
                flagged = flags.get(flag_key)
                if isinstance(flagged, dict):
                    if isinstance(default_guide, dict):
                        merged = dict(default_guide)
                        merged.update(flagged)
                        return merged
                    return flagged
        # 単独フラグ
        for flag_name in active_flags:
            flagged = flags.get(flag_name)
            if isinstance(flagged, dict):
                if isinstance(default_guide, dict):
                    merged = dict(default_guide)
                    merged.update(flagged)
                    return merged
                return flagged
    return default_guide if isinstance(default_guide, dict) else None


def get_zone_guide(guide_data: dict, zone_id: str, visit: int = 1, config: dict | None = None, active_flags: set[str] | None = None) -> dict | None:
    """
    ゾーンIDからガイドを検索（ルート対応版 + 構造化フラグ対応）

    検索優先順位:
    1. {zone_id}~{route}@{visit} (ルート指定+訪問回数)
    2. {zone_id}~{route}         (ルート指定+1回目)
    3. {zone_id}@{visit}         (デフォルト+訪問回数)
    4. {zone_id}                 (デフォルト)

    各エントリは従来形式の guide dict でも、
    {"default": {...}, "flags": {"boss_dead": {...}}} の構造化形式でもよい。
    """
    base_guide = guide_data.get(zone_id)
    route = _get_route_for_zone(zone_id, config)

    candidates = []
    if route and visit >= 2:
        candidates.append(f"{zone_id}~{route}@{visit}")
        candidates.append(f"{zone_id}~{route}@2")
    if route:
        candidates.append(f"{zone_id}~{route}")
    if visit >= 2:
        for v in [visit, 2]:
            candidates.append(f"{zone_id}@{v}")
    candidates.append(zone_id)

    resolved_base = _resolve_structured_flag_guide(base_guide, active_flags) if isinstance(base_guide, dict) else base_guide

    for key in candidates:
        guide = guide_data.get(key)
        if not guide:
            continue
        if isinstance(guide, dict) and ("default" in guide or "flags" in guide):
            guide = _resolve_structured_flag_guide(guide, active_flags)
            if not guide:
                continue
        # directionが未設定ならbase_guideから継承
        if "direction" not in guide and isinstance(resolved_base, dict) and "direction" in resolved_base:
            guide = {**guide, "direction": resolved_base["direction"]}
        return guide

    return None


DIRECTION_ARROWS = {
    "n": "⬆", "s": "⬇", "e": "➡", "w": "⬅",
    "ne": "⬈", "nw": "⬉", "se": "⬊", "sw": "⬋",
    "none": None,
}


def _safe_html(text: str) -> str:
    """HTMLエスケープしつつ、<span style='color:...'> と </span> だけ許可"""
    escaped = html.escape(text)
    # エスケープされた color span タグを復元
    escaped = re.sub(
        r"&lt;span style=(?:&#x27;|&quot;)\s*color:\s*(#[0-9a-fA-F]{3,8})\s*;?\s*(?:&#x27;|&quot;)\s*&gt;",
        r"<span style='color:\1'>",
        escaped,
        flags=re.IGNORECASE,
    )
    escaped = escaped.replace("&lt;/span&gt;", "</span>")
    # ダブルクォートはHTMLコンテンツ内では無害なので戻す
    escaped = escaped.replace("&quot;", '"')
    escaped = escaped.replace("&#x27;", "'")
    return escaped


def format_guide_html(guide: dict, font_size: int = 12, show_direction: bool = True) -> str:
    """ガイドデータをHTML形式にフォーマット"""
    if not guide:
        return ""
    
    parts = []
    
    # 方向矢印HTMLを先に作っておく（objectiveの後に挿入）
    direction = guide.get("direction", "")
    direction_html = ""
    if show_direction and direction and direction != "none":
        arrow = DIRECTION_ARROWS.get(direction, "")
        if arrow:
            arrow_size = max(font_size * 3, 36)
            direction_html = (
                f"<div style='margin: 4px 0;'>"
                f"<b style='color:#b0ff7b; font-size:{font_size}px;'>🧭 基本方向</b><br>"
                f"<span style='font-size:{arrow_size}px; color:#FF69B4;'>{arrow}</span>"
                f"</div>"
            )
    elif show_direction and direction == "none":
        direction_html = (
            f"<div style='margin: 4px 0;'>"
            f"<b style='color:#b0ff7b; font-size:{font_size}px;'>🧭 基本方向</b><br>"
            f"<span style='font-size:{font_size + 2}px; color:#888888;'>📖 ガイド参照</span>"
            f"</div>"
        )
    
    objective = guide.get("objective", "")
    if objective:
        obj_html = _safe_html(objective.strip()).replace("\n", "<br>")
        obj_html = obj_html.replace("　", "&nbsp;&nbsp;")
        obj_html = obj_html.replace("  ", "&nbsp;&nbsp;")
        parts.append(
            f"<p style='margin:0;'>"
            f"<b style='color:#b0ff7b; font-size:{font_size}px;'>📋 目標</b><br>"
            f"<span style='color:#ffffff;'>{obj_html}</span>"
            f"</p>"
        )
    
    # 目標の後に基本方向を挿入
    if direction_html:
        parts.append(direction_html)
    
    layout = guide.get("layout", "")
    if layout:
        # 改行をbrに変換、全角スペースのインデントを保持
        layout_html = _safe_html(layout.strip()).replace("\n", "<br>")
        layout_html = layout_html.replace("　", "&nbsp;&nbsp;")  # 全角スペース→2つのnbsp
        layout_html = layout_html.replace("  ", "&nbsp;&nbsp;")  # 半角2連続スペースも保持
        parts.append(f"<p style='margin:0;'><b style='color:#b0ff7b;'>🗺️ レイアウト情報</b><br>{layout_html}</p>")
    
    tips = guide.get("tips", "")
    if tips:
        tips_html = _safe_html(tips.strip()).replace("\n", "<br>")
        tips_html = tips_html.replace("　", "&nbsp;&nbsp;")
        tips_html = tips_html.replace("  ", "&nbsp;&nbsp;")
        parts.append(f"<p style='margin:0;'><b style='color:#b0ff7b;'>💡 Tips / 注意点</b><br><span style='color:#ffffff;'>{tips_html}</span></p>")
    
    return "<span style='font-size:6px; line-height:50%;'><br></span>".join(parts)
