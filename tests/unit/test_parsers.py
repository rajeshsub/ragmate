"""Unit tests for document parsers."""

from __future__ import annotations

from pathlib import Path

import pytest

from ragmate.core.ingestion.parsers import parse_document


def test_parse_txt(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("Hello from txt", encoding="utf-8")
    assert parse_document(f) == "Hello from txt"


def test_parse_md(tmp_path: Path) -> None:
    f = tmp_path / "test.md"
    f.write_text("# Heading\nSome content", encoding="utf-8")
    result = parse_document(f)
    assert "Heading" in result
    assert "Some content" in result


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    f = tmp_path / "test.csv"
    f.write_text("a,b,c")
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_document(f)


def test_parse_docx(tmp_path: Path) -> None:
    pytest.importorskip("docx")
    from docx import Document

    f = tmp_path / "test.docx"
    doc = Document()
    doc.add_paragraph("Docx content here")
    doc.save(str(f))
    result = parse_document(f)
    assert "Docx content here" in result
