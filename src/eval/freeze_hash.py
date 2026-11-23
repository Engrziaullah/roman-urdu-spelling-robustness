"""Print the frozen-items hash line required by FROZEN.md and the runner."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def normalized_bytes_sha256(data: bytes) -> str:
    """Hash UTF-8 bytes after normalizing CRLF line endings to LF."""
    normalized = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def normalized_items_sha256(path: str | Path) -> str:
    """Hash UTF-8 text after normalizing CRLF line endings to LF."""
    file_path = Path(path)
    return normalized_bytes_sha256(file_path.read_bytes())


def normalized_items_sha256_from_git_ref(ref: str, path: str | Path, cwd: str | Path | None = None) -> str:
    """Hash a git object at ``ref:path`` by reading bytes in binary mode.

    Uses ``git show`` via ``subprocess.run(..., capture_output=True)`` so the
    bytes are not re-encoded by a shell/PowerShell pipeline.
    """
    spec = f"{ref}:{path}"
    result = subprocess.run(["git", "show", spec], capture_output=True, cwd=cwd)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git show {spec} failed (exit {result.returncode}): {stderr}")
    return normalized_bytes_sha256(result.stdout)


def freeze_hash_line(path: str | Path, *, git_ref: str | None = None) -> str:
    """Return the exact FROZEN.md line for the given items file."""
    if git_ref:
        digest = normalized_items_sha256_from_git_ref(git_ref, path)
    else:
        digest = normalized_items_sha256(path)
    return f"items_v1.jsonl sha256: {digest}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Path to the items JSONL file to hash.")
    parser.add_argument(
        "--git-ref",
        help=(
            "Optional git ref (commit/branch/tag) to hash as <ref>:<file> via "
            "binary 'git show' output instead of reading the working-tree file."
        ),
    )
    args = parser.parse_args(argv)
    print(freeze_hash_line(args.file, git_ref=args.git_ref))
    return 0


if __name__ == "__main__":
    sys.exit(main())
