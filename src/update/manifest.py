import hashlib
import json
from pathlib import Path
import shutil


MANIFEST_NAME = "update-manifest.json"
MUTABLE_PATHS = tuple(
    Path(value)
    for value in (
        "guide_data.json",
        "guide_data_poe2.json",
        "data/zone_data.json",
        "_internal/guide_data.json",
        "_internal/guide_data_poe2.json",
        "_internal/data/zone_data.json",
    )
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: Path, version: str) -> dict:
    files = {
        path.as_posix(): _sha256(root / path)
        for path in MUTABLE_PATHS
        if (root / path).is_file()
    }
    return {
        "schema": 1,
        "version": version,
        "mutable_files": files,
    }


def write_manifest(root: Path, version: str) -> Path:
    target = root / MANIFEST_NAME
    target.write_text(
        json.dumps(build_manifest(root, version), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def preserve_modified_files(old_root: Path, new_root: Path) -> list[Path]:
    manifest_path = old_root / MANIFEST_NAME
    try:
        old_hashes = json.loads(
            manifest_path.read_text(encoding="utf-8")
        ).get("mutable_files", {})
        has_manifest = True
    except (OSError, ValueError, TypeError):
        old_hashes = {}
        has_manifest = False

    preserved = []
    for relative in MUTABLE_PATHS:
        source = old_root / relative
        destination = new_root / relative
        if not source.is_file() or not destination.is_file():
            continue
        expected = old_hashes.get(relative.as_posix())
        modified = (
            not has_manifest
            or expected is None
            or _sha256(source) != expected
        )
        if modified:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            preserved.append(relative)
    return preserved
