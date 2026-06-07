"""Shared fixtures across all test layers."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set env vars before any app import
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("API_KEY", "test-api-key")


@pytest.fixture
def tmp_chroma_dir(tmp_path: Path) -> Path:
    return tmp_path / "chroma"


@pytest.fixture
def settings(tmp_chroma_dir: Path, tmp_path: Path):  # type: ignore[no-untyped-def]
    from ragmate.config import Settings

    return Settings(
        gemini_api_key="test-gemini-key",
        api_key="test-api-key",
        chroma_persist_dir=tmp_chroma_dir,
        upload_dir=tmp_path / "uploads",
    )


@pytest.fixture
def vector_store(settings):  # type: ignore[no-untyped-def]
    from ragmate.core.storage.chroma import VectorStore

    return VectorStore(settings.chroma_persist_dir)


@pytest.fixture
def mock_embedder():  # type: ignore[no-untyped-def]
    with patch("ragmate.core.ingestion.embedder.genai") as mock_genai:
        mock_genai.embed_content.return_value = {"embedding": [[0.1] * 768]}
        yield mock_genai


@pytest.fixture
def mock_generator():  # type: ignore[no-untyped-def]
    with patch("ragmate.core.retrieval.generator.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text="Test answer.")
        mock_genai.GenerativeModel.return_value = mock_model
        yield mock_genai


@pytest.fixture
def api_client(settings, tmp_chroma_dir) -> Generator[TestClient]:  # type: ignore[no-untyped-def]
    from ragmate.api.dependencies import get_settings as dep_settings
    from ragmate.api.dependencies import get_vector_store
    from ragmate.core.storage.chroma import VectorStore
    from ragmate.main import app

    store = VectorStore(tmp_chroma_dir)

    app.dependency_overrides[dep_settings] = lambda: settings
    app.dependency_overrides[get_vector_store] = lambda: store

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
