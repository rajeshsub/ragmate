"""ChromaDB client: vectors + document metadata."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

_DOCUMENTS_COLLECTION = "documents"
_META_COLLECTION = "document_meta"


class VectorStore:
    def __init__(self, persist_dir: Path) -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._chunks = self._client.get_or_create_collection(
            name=_DOCUMENTS_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        self._meta = self._client.get_or_create_collection(name=_META_COLLECTION)

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def add_document(
        self,
        doc_id: str,
        filename: str,
        chunks: list[str],
        embeddings: list[list[float]],
        extra_meta: dict[str, Any] | None = None,
    ) -> None:
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
        self._chunks.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)  # type: ignore[arg-type]

        doc_meta: dict[str, Any] = {
            "filename": filename,
            "chunk_count": len(chunks),
            "uploaded_at": datetime.now(UTC).isoformat(),
        }
        if extra_meta:
            doc_meta.update(extra_meta)

        self._meta.add(
            ids=[doc_id],
            documents=[filename],
            metadatas=[doc_meta],
        )

    def delete_document(self, doc_id: str) -> bool:
        """Returns False if document not found."""
        existing = self._meta.get(ids=[doc_id])
        if not existing["ids"]:
            return False

        chunk_results = self._chunks.get(where={"doc_id": doc_id})
        if chunk_results["ids"]:
            self._chunks.delete(ids=chunk_results["ids"])

        self._meta.delete(ids=[doc_id])
        return True

    def list_documents(self) -> list[dict[str, Any]]:
        results = self._meta.get(include=["metadatas", "documents"])
        docs = []
        for doc_id, meta in zip(results["ids"], results["metadatas"] or [], strict=False):
            docs.append({"id": doc_id, **(meta or {})})
        return docs

    def document_exists(self, doc_id: str) -> bool:
        return bool(self._meta.get(ids=[doc_id])["ids"])

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        results = self._chunks.query(
            query_embeddings=[embedding],  # type: ignore[arg-type]
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        output = []
        docs = results.get("documents") or [[]]
        metas = results.get("metadatas") or [[]]
        dists = results.get("distances") or [[]]
        for text, meta, dist in zip(docs[0], metas[0], dists[0], strict=False):
            output.append(
                {
                    "text": text,
                    "doc_id": (meta or {}).get("doc_id", ""),
                    "chunk_index": (meta or {}).get("chunk_index", 0),
                    "score": 1.0 - float(dist),
                }
            )
        return output

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def new_doc_id() -> str:
        return str(uuid.uuid4())
