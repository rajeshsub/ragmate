"""Integration tests for ingestion pipeline with real ChromaDB, mocked Gemini."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragmate.config import Settings
from ragmate.core.ingestion.pipeline import IngestionPipeline
from ragmate.core.storage.chroma import VectorStore


@pytest.fixture
def store(tmp_path: Path) -> VectorStore:
    return VectorStore(tmp_path / "chroma")


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        gemini_api_key="test",
        api_key="test",
        chroma_persist_dir=tmp_path / "chroma",
        upload_dir=tmp_path / "uploads",
    )


def _mock_embedder_patch() -> patch:  # type: ignore[type-arg]
    m = MagicMock()
    m.embed_texts.return_value = [[0.1] * 768]
    return patch("ragmate.core.ingestion.pipeline.Embedder", return_value=m)


def test_ingest_txt_file(tmp_path: Path, settings: Settings, store: VectorStore) -> None:
    doc = tmp_path / "doc.txt"
    doc.write_text("This is test content for ingestion.", encoding="utf-8")

    with _mock_embedder_patch():
        pipeline = IngestionPipeline(settings=settings, store=store)
        result = pipeline.ingest(doc, "doc.txt")

    assert result["filename"] == "doc.txt"
    assert result["chunk_count"] >= 1
    assert store.document_exists(result["id"])


def test_ingest_empty_file_raises(tmp_path: Path, settings: Settings, store: VectorStore) -> None:
    doc = tmp_path / "empty.txt"
    doc.write_text("", encoding="utf-8")

    with _mock_embedder_patch():
        pipeline = IngestionPipeline(settings=settings, store=store)
        with pytest.raises(ValueError, match="no text chunks"):
            pipeline.ingest(doc, "empty.txt")
