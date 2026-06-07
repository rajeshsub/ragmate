"""Orchestrates parse → chunk → embed → store for a single document."""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ragmate.config import Settings
from ragmate.core.ingestion.chunker import split_text
from ragmate.core.ingestion.embedder import _BATCH_SIZE, Embedder
from ragmate.core.ingestion.parsers import parse_document
from ragmate.core.storage.chroma import VectorStore

log = logging.getLogger(__name__)

OnProgress = Callable[[dict[str, Any]], None]


class IngestionPipeline:
    def __init__(self, settings: Settings, store: VectorStore) -> None:
        self._settings = settings
        self._store = store
        self._embedder = Embedder(settings)

    def ingest(
        self,
        file_path: Path,
        filename: str,
        on_progress: OnProgress | None = None,
    ) -> dict[str, Any]:
        def emit(stage: str, pct: int, message: str) -> None:
            log.info("[ingest] %s (%d%%)", message, pct)
            if on_progress:
                on_progress({"stage": stage, "pct": pct, "message": message})

        doc_id = VectorStore.new_doc_id()

        emit("parsing", 5, f"Parsing {filename}…")
        text = parse_document(file_path)
        log.info("[ingest] parsed %d chars", len(text))

        emit("chunking", 15, "Splitting into chunks…")
        chunks = split_text(
            text,
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )

        if not chunks:
            raise ValueError("Document produced no text chunks - file may be empty or unreadable.")

        n_batches = math.ceil(len(chunks) / _BATCH_SIZE)
        emit("embedding", 20, f"Embedding {len(chunks)} chunks in {n_batches} batch(es)…")

        def embed_progress(batch_num: int, total_batches: int) -> None:
            pct = 20 + int(batch_num / total_batches * 70)
            emit("embedding", pct, f"Embedding batch {batch_num}/{total_batches}…")

        embeddings = self._embedder.embed_texts(chunks, on_progress=embed_progress)

        emit("storing", 92, "Storing vectors in ChromaDB…")
        self._store.add_document(
            doc_id=doc_id,
            filename=filename,
            chunks=chunks,
            embeddings=embeddings,
        )

        log.info("[ingest] done. doc_id=%s chunks=%d", doc_id, len(chunks))
        return {"id": doc_id, "filename": filename, "chunk_count": len(chunks)}
