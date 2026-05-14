"""
PoBインポーター: PoBエクスポートコード(Base64)をパースしてジェム情報を抽出する。

PoBのエクスポートコード:
  Base64 → zlib解凍 → XML文字列

XMLの構造(PoE1):
  <PathOfBuilding>
    <Build className="Shadow" ascendClassName="Assassin" ...>
    <Skills>
      <SkillSet title="...">
        <Skill label="Main Skill" ...>
          <Gem nameSpec="Blade Vortex" ... />
          <Gem nameSpec="Unleash Support" skillId="SupportUnleash" ... />
        </Skill>
      </SkillSet>
    </Skills>
  </PathOfBuilding>
"""

import base64
import zlib
import re
import html


# PoE1クラス → 昇華クラス マッピング
ASCENDANCY_MAP = {
    "scion": ["ascendant"],
    "marauder": ["juggernaut", "berserker", "chieftain"],
    "ranger": ["deadeye", "pathfinder", "warden"],
    "witch": ["occultist", "elementalist", "necromancer"],
    "duelist": ["slayer", "gladiator", "champion"],
    "templar": ["inquisitor", "hierophant", "guardian"],
    "shadow": ["assassin", "trickster", "saboteur"],
}

# 昇華クラス名 → 基本クラス名の逆引き
_ASCENDANCY_TO_CLASS = {}
for base_class, ascendancies in ASCENDANCY_MAP.items():
    for asc in ascendancies:
        _ASCENDANCY_TO_CLASS[asc] = base_class


def decode_pob_code(pob_code: str) -> str:
    """PoBコードをBase64デコード→zlibデコードしてXML文字列を返す"""
    # 空白・改行を除去
    pob_code = pob_code.strip().replace("\n", "").replace("\r", "")
    
    # Base64のパディング調整
    missing_padding = len(pob_code) % 4
    if missing_padding:
        pob_code += "=" * (4 - missing_padding)
    
    # PoBはURL-safe Base64を使用
    try:
        compressed = base64.urlsafe_b64decode(pob_code)
    except Exception:
        # 通常のBase64も試す
        compressed = base64.b64decode(pob_code)
    
    # zlib解凍
    xml_bytes = zlib.decompress(compressed)
    xml_str = xml_bytes.decode("utf-8")
    
    return xml_str


def parse_pob_xml(xml_str: str) -> dict:
    """
    PoBのXMLからクラス・ジェム情報を抽出する。
    
    Returns:
        {
            "class": "shadow",
            "ascendancy": "assassin",
            "gem_names": ["blade vortex", "unleash support", ...],
            "gem_groups": [
                {
                    "label": "Main Skill",
                    "gems": [
                        {"name": "blade vortex", "is_support": False},
                        {"name": "unleash support", "is_support": True},
                    ]
                },
                ...
            ]
        }
    """
    # HTML エンティティをデコード
    xml_str = html.unescape(xml_str)
    
    # クラス名抽出
    class_match = re.search(r'className="([^"]*)"', xml_str, re.IGNORECASE)
    class_name = class_match.group(1).lower() if class_match else ""
    
    # 昇華クラス名抽出
    asc_match = re.search(r'ascendClassName="([^"]*)"', xml_str, re.IGNORECASE)
    ascendancy = asc_match.group(1).lower() if asc_match else ""
    
    # 昇華クラス名が「None」の場合はクリア
    if ascendancy == "none":
        ascendancy = ""
    
    # 昇華名から基本クラスを推測（classNameが空の場合）
    if not class_name and ascendancy and ascendancy in _ASCENDANCY_TO_CLASS:
        class_name = _ASCENDANCY_TO_CLASS[ascendancy]
    
    # ジェム抽出
    gem_groups = []
    gem_names_set = set()
    
    # <Skill> ブロックを抽出
    skill_pattern = re.compile(
        r'<Skill\s[^>]*label="([^"]*)"[^>]*>(.*?)</Skill>',
        re.IGNORECASE | re.DOTALL
    )
    # 自己完結型のSkill（ジェムなし）は無視
    
    for skill_match in skill_pattern.finditer(xml_str):
        label = skill_match.group(1)
        skill_body = skill_match.group(2)
        
        # <Gem> タグを抽出
        gem_pattern = re.compile(
            r'<Gem\s[^>]*nameSpec="([^"]*)"[^>]*/?>',
            re.IGNORECASE
        )
        
        gems = []
        for gem_match in gem_pattern.finditer(skill_body):
            name_spec = gem_match.group(1).strip()
            if not name_spec:
                continue
            
            # nameSpecからジェム名を正規化
            gem_name = _normalize_gem_name(name_spec, gem_match.group(0))
            is_support = _is_support_gem(gem_match.group(0), gem_name)
            
            gems.append({
                "name": gem_name,
                "is_support": is_support,
            })
            gem_names_set.add(gem_name)
        
        if gems:
            gem_groups.append({
                "label": label,
                "gems": gems,
            })
    
    # label なしの <Skill> も処理（label="" のケース）
    skill_no_label_pattern = re.compile(
        r'<Skill\s(?:(?!label=)[^>])*>(.*?)</Skill>',
        re.IGNORECASE | re.DOTALL
    )
    for skill_match in skill_no_label_pattern.finditer(xml_str):
        skill_body = skill_match.group(1)
        gem_pattern = re.compile(
            r'<Gem\s[^>]*nameSpec="([^"]*)"[^>]*/?>',
            re.IGNORECASE
        )
        gems = []
        for gem_match in gem_pattern.finditer(skill_body):
            name_spec = gem_match.group(1).strip()
            if not name_spec:
                continue
            gem_name = _normalize_gem_name(name_spec, gem_match.group(0))
            is_support = _is_support_gem(gem_match.group(0), gem_name)
            gems.append({"name": gem_name, "is_support": is_support})
            gem_names_set.add(gem_name)
        if gems:
            gem_groups.append({"label": "", "gems": gems})
    
    return {
        "class": class_name,
        "ascendancy": ascendancy,
        "gem_names": sorted(gem_names_set),
        "gem_groups": gem_groups,
    }


def _normalize_gem_name(name_spec: str, gem_tag: str) -> str:
    """ジェム名を正規化（小文字、Vaal/Awakened除去など）"""
    name = name_spec.lower().strip()
    
    # 「Vaal 」「Awakened 」プレフィクス除去
    name = re.sub(r'^vaal\s+', '', name)
    name = re.sub(r'^awakened\s+', '', name)
    
    # コロン以降を除去（「Herald of Ice: Elementalist」など）
    if ':' in name:
        name = name[:name.index(':')].strip()
    
    # 「of」以降のサブスキル名を処理（gems.jsonに一致しない場合のフォールバック）
    # 例: "Herald of Ice" → そのまま保持（gems.jsonに存在）
    
    return name


def _is_support_gem(gem_tag: str, gem_name: str) -> bool:
    """サポートジェムかどうか判定"""
    # skillIdに /supportgem が含まれる
    if '/supportgem' in gem_tag.lower():
        return True
    if 'support' in gem_tag.lower() and 'skillid' in gem_tag.lower():
        skill_id_match = re.search(r'skillId="([^"]*)"', gem_tag, re.IGNORECASE)
        if skill_id_match and 'support' in skill_id_match.group(1).lower():
            return True
    # ジェム名に "support" が含まれる
    if 'support' in gem_name:
        return True
    return False


def import_pob(pob_code: str) -> dict:
    """
    PoBコードをインポートしてジェム情報を返す。
    
    Args:
        pob_code: PoBのBase64エクスポートコード
        
    Returns:
        parse_pob_xml() の結果
        
    Raises:
        ValueError: デコードやパースに失敗した場合
    """
    try:
        xml_str = decode_pob_code(pob_code)
    except Exception as e:
        raise ValueError(f"PoBコードのデコードに失敗しました: {e}")
    
    if "<pathofbuilding>" not in xml_str.lower():
        raise ValueError("有効なPoBデータではありません（PathOfBuildingタグが見つかりません）")
    
    result = parse_pob_xml(xml_str)
    
    if not result["class"]:
        raise ValueError("クラス情報が見つかりません")
    if not result["gem_names"]:
        raise ValueError("ジェム情報が見つかりません")
    
    return result
