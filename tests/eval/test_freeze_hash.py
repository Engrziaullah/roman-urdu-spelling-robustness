from __future__ import annotations

from pathlib import Path

from src.eval.freeze_hash import freeze_hash_line, normalized_items_sha256


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
