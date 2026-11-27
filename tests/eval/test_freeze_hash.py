from __future__ import annotations

import subprocess
from pathlib import Path

from src.eval.freeze_hash import (
    freeze_hash_line,
    normalized_bytes_sha256,
    normalized_items_sha256,
    normalized_items_sha256_from_git_ref,
)


def test_freeze_hash_normalizes_crlf_to_lf(tmp_path: Path) -> None:
    lf = tmp_path / "lf.jsonl"
    crlf = tmp_path / "crlf.jsonl"
    content_lf = b'{"item_id":"x"}\n{"item_id":"y"}\n'
    content_crlf = b'{"item_id":"x"}\r\n{"item_id":"y"}\r\n'
    lf.write_bytes(content_lf)
    crlf.write_bytes(content_crlf)
    assert normalized_items_sha256(lf) == normalized_items_sha256(crlf)


def test_freeze_hash_line_format(tmp_path: Path) -> None:
    items = tmp_path / "items_v1.jsonl"
    items.write_text('{"item_id":"x"}\n', encoding="utf-8")
    digest = normalized_items_sha256(items)
    assert freeze_hash_line(items) == f"items_v1.jsonl sha256: {digest}"
    assert len(digest) == 64


def test_normalized_bytes_sha256_matches_file(tmp_path: Path) -> None:
    items = tmp_path / "items.jsonl"
    raw = b'{"item_id":"x"}\r\n'
    items.write_bytes(raw)
    assert normalized_bytes_sha256(raw) == normalized_items_sha256(items)


def test_freeze_hash_from_git_ref_matches_file_bytes(tmp_path: Path) -> None:
    """Hashing a committed blob via --git-ref must equal hashing its bytes."""
    items = tmp_path / "items_v1.jsonl"
    raw = b'{"item_id":"x"}\n{"item_id":"y"}\n'
    items.write_bytes(raw)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "items_v1.jsonl"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    digest = normalized_items_sha256(items)
    assert normalized_items_sha256_from_git_ref("HEAD", "items_v1.jsonl", cwd=tmp_path) == digest
    assert freeze_hash_line(tmp_path / "items_v1.jsonl") == f"items_v1.jsonl sha256: {digest}"
