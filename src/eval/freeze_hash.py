"""Print the frozen-items hash line required by FROZEN.md and the runner."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Sequence


def normalized_items_sha256(path: str | Path) -> str:
    """Hash UTF-8 text after normalizing CRLF line endings to LF."""
    file_path = Path(path)
    with file_path.open(encoding="utf-8", newline="") as file:
        normalized = file.read().replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def freeze_hash_line(path: str | Path) -> str:
    """Return the exact FROZEN.md line for the given items file."""
    return f"items_v1.jsonl sha256: {normalized_items_sha256(path)}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Path to the items JSONL file to hash.")
    args = parser.parse_args(argv)
    print(freeze_hash_line(args.file))
    return 0


if __name__ == "__main__":
    sys.exit(main())
