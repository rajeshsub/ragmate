"""Integration tests for VectorStore against real ChromaDB (tmp dir)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ragmate.core.storage.chroma import VectorStore


@pytest.fixture
def store(tmp_path: Path) -> VectorStore:
    return VectorStore(tmp_path / "chroma")


def _fake_embeddings(n: int) -> list[list[float]]:
    return [[float(i) * 0.01] * 768 for i in range(n)]


def test_add_and_list_document(store: VectorStore) -> None:
    store.add_document(
        doc_id="doc1",
        filename="test.txt",
        chunks=["chunk one", "chunk two"],
        embeddings=_fake_embeddings(2),
    )
    docs = store.list_documents()
    assert len(docs) == 1
    assert docs[0]["id"] == "doc1"
    assert docs[0]["filename"] == "test.txt"
    assert docs[0]["chunk_count"] == 2


def test_delete_existing_document(store: VectorStore) -> None:
    store.add_document("doc1", "f.txt", ["text"], _fake_embeddings(1))
    deleted = store.delete_document("doc1")
    assert deleted is True
    assert store.list_documents() == []


def test_delete_nonexistent_returns_false(store: VectorStore) -> None:
    assert store.delete_document("nonexistent") is False


def test_document_exists(store: VectorStore) -> None:
    store.add_document("doc1", "f.txt", ["text"], _fake_embeddings(1))
    assert store.document_exists("doc1") is True
    assert store.document_exists("other") is False


def test_query_returns_results(store: VectorStore) -> None:
    store.add_document("doc1", "f.txt", ["relevant text"], _fake_embeddings(1))
    results = store.query([0.0] * 768, top_k=1)
    assert len(results) == 1
    assert results[0]["text"] == "relevant text"
    assert results[0]["doc_id"] == "doc1"
    assert 0.0 <= results[0]["score"] <= 1.0


def test_query_empty_store_returns_empty(store: VectorStore) -> None:
    results = store.query([0.0] * 768, top_k=5)
    assert results == []


def test_multiple_documents_listed(store: VectorStore) -> None:
    store.add_document("doc1", "a.txt", ["chunk"], _fake_embeddings(1))
    store.add_document("doc2", "b.txt", ["chunk"], _fake_embeddings(1))
    docs = store.list_documents()
    ids = {d["id"] for d in docs}
    assert ids == {"doc1", "doc2"}
