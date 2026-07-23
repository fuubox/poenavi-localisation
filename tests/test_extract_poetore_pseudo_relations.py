from scripts.extract_poetore_pseudo_relations import extract_relations


def test_extract_relations_reads_group_and_replaces_without_inner_object_confusion():
    source = """
const PSEUDO_RULES: PseudoRule[] = [
  { pseudo: stat('General'), group: 'damage', stats: [{ ref: stat('A') }] },
  { pseudo: stat('Specific'), replaces: 'damage', stats: [{ ref: stat('B') }] }
]

export function filterPseudo () {}
"""
    assert extract_relations(source) == [
        {"order": 0, "pseudo_ref": "General", "group": "damage"},
        {"order": 1, "pseudo_ref": "Specific", "replaces": "damage"},
    ]
