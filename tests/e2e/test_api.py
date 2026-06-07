"""E2E tests hitting the FastAPI endpoints via TestClient."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from ragmate.config import Settings
from ragmate.core.storage.chroma import VectorStore


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        gemini_api_key="test",
        api_key="test-api-key",
        chroma_persist_dir=tmp_path / "chroma",
        upload_dir=tmp_path / "uploads",
    )


@pytest.fixture
def store(settings: Settings) -> VectorStore:
    return VectorStore(settings.chroma_persist_dir)


@pytest.fixture
def client(settings: Settings, store: VectorStore) -> TestClient:
    from ragmate.api.dependencies import get_settings as dep_get_settings
    from ragmate.api.dependencies import get_vector_store
    from ragmate.main import app

    app.dependency_overrides[dep_get_settings] = lambda: settings
    app.dependency_overrides[get_vector_store] = lambda: store

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


HEADERS = {"X-API-Key": "test-api-key"}


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------


def test_missing_api_key_returns_401(client: TestClient) -> None:
    r = client.get("/documents")
    assert r.status_code == 401


def test_wrong_api_key_returns_401(client: TestClient) -> None:
    r = client.get("/documents", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


# ------------------------------------------------------------------
# Documents
# ------------------------------------------------------------------


def test_list_documents_empty(client: TestClient) -> None:
    r = client.get("/documents", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["documents"] == []


def test_upload_unsupported_format(client: TestClient) -> None:
    r = client.post(
        "/documents",
        headers=HEADERS,
        files={"file": ("test.csv", b"a,b,c", "text/csv")},
    )
    assert r.status_code == 422


def test_upload_txt_document(client: TestClient) -> None:
    from ragmate.api.dependencies import get_ingestion_pipeline
    from ragmate.main import app

    mock_pipeline = MagicMock()
    mock_pipeline.ingest.return_value = {
        "id": "abc123",
        "filename": "notes.txt",
        "chunk_count": 3,
    }
    app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_pipeline

    r = client.post(
        "/documents",
        headers=HEADERS,
        files={"file": ("notes.txt", b"Hello world content", "text/plain")},
    )

    app.dependency_overrides.pop(get_ingestion_pipeline, None)

    assert r.status_code == 200
    events = [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]
    done = next((e for e in events if e["stage"] == "done"), None)
    assert done is not None
    assert done["id"] == "abc123"
    assert done["chunk_count"] == 3


def test_delete_nonexistent_document(client: TestClient) -> None:
    r = client.delete("/documents/nonexistent-id", headers=HEADERS)
    assert r.status_code == 404


def test_delete_existing_document(client: TestClient, store: VectorStore) -> None:
    store.add_document("doc1", "f.txt", ["content"], [[0.1] * 768])
    r = client.delete("/documents/doc1", headers=HEADERS)
    assert r.status_code == 204


# ------------------------------------------------------------------
# Query
# ------------------------------------------------------------------


def test_query_empty_store(client: TestClient) -> None:
    from ragmate.api.dependencies import get_retrieval_pipeline
    from ragmate.main import app

    mock_pipeline = MagicMock()
    mock_pipeline.query.return_value = {
        "answer": "No relevant documents found. Please upload documents first.",
        "sources": [],
    }
    app.dependency_overrides[get_retrieval_pipeline] = lambda: mock_pipeline

    r = client.post("/query", headers=HEADERS, json={"question": "What is this about?"})

    app.dependency_overrides.pop(get_retrieval_pipeline, None)

    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["sources"] == []


def test_query_returns_answer_and_sources(client: TestClient) -> None:
    from ragmate.api.dependencies import get_retrieval_pipeline
    from ragmate.main import app

    mock_pipeline = MagicMock()
    mock_pipeline.query.return_value = {
        "answer": "The answer is 42.",
        "sources": [
            {"doc_id": "doc1", "chunk_index": 0, "score": 0.95, "excerpt": "relevant text..."}
        ],
    }
    app.dependency_overrides[get_retrieval_pipeline] = lambda: mock_pipeline

    r = client.post("/query", headers=HEADERS, json={"question": "What is the answer?"})

    app.dependency_overrides.pop(get_retrieval_pipeline, None)

    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "The answer is 42."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["score"] == 0.95


def test_query_empty_question_rejected(client: TestClient) -> None:
    r = client.post("/query", headers=HEADERS, json={"question": ""})
    assert r.status_code == 422
