import argparse
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.update.manifest import write_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("version")
    args = parser.parse_args()
    write_manifest(args.root.resolve(), args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
