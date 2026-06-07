"""Orchestrates embed query → vector search → generate answer."""

from __future__ import annotations

from typing import Any

from ragmate.config import Settings
from ragmate.core.ingestion.embedder import Embedder
from ragmate.core.retrieval.generator import Generator
from ragmate.core.storage.chroma import VectorStore


class RetrievalPipeline:
    def __init__(self, settings: Settings, store: VectorStore) -> None:
        self._settings = settings
        self._store = store
        self._embedder = Embedder(settings)
        self._generator = Generator(settings)
        self._cache: dict[str, dict[str, Any]] = {}

    def query(self, question: str) -> dict[str, Any]:
        cache_key = question.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        embedding = self._embedder.embed_query(question)
        chunks = self._store.query(embedding, top_k=self._settings.top_k_results)

        if not chunks:
            return {
                "answer": "No relevant documents found. Please upload documents first.",
                "sources": [],
            }

        answer = self._generator.generate(question, chunks)

        sources = [
            {
                "doc_id": c["doc_id"],
                "chunk_index": c["chunk_index"],
                "score": round(c["score"], 4),
                "excerpt": c["text"][:200] + ("..." if len(c["text"]) > 200 else ""),
            }
            for c in chunks
        ]

        result: dict[str, Any] = {"answer": answer, "sources": sources}
        self._cache[cache_key] = result
        return result
