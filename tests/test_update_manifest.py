from pathlib import Path

from src.update.manifest import preserve_modified_files, write_manifest


def seed(root: Path, relative: str, content: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_unmodified_mutable_file_uses_new_release_content(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    seed(old, "guide_data.json", "old-default")
    seed(new, "guide_data.json", "new-default")
    write_manifest(old, "2.4.0")

    assert preserve_modified_files(old, new) == []
    assert (new / "guide_data.json").read_text(encoding="utf-8") == "new-default"


def test_modified_mutable_file_is_copied_to_new_release(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    seed(old, "guide_data.json", "old-default")
    write_manifest(old, "2.4.0")
    (old / "guide_data.json").write_text("user-edit", encoding="utf-8")
    seed(new, "guide_data.json", "new-default")

    assert preserve_modified_files(old, new) == [Path("guide_data.json")]
    assert (new / "guide_data.json").read_text(encoding="utf-8") == "user-edit"


def test_missing_old_manifest_preserves_known_mutable_files(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    seed(old, "_internal/data/zone_data.json", "legacy-user-data")
    seed(new, "_internal/data/zone_data.json", "new-default")

    assert preserve_modified_files(old, new) == [
        Path("_internal/data/zone_data.json")
    ]
    assert (new / "_internal/data/zone_data.json").read_text(
        encoding="utf-8"
    ) == "legacy-user-data"
