"""FastAPI dependency providers for shared resources."""

from __future__ import annotations

from functools import lru_cache

from ragmate.config import get_settings as get_settings
from ragmate.core.ingestion.pipeline import IngestionPipeline
from ragmate.core.retrieval.pipeline import RetrievalPipeline
from ragmate.core.storage.chroma import VectorStore


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return VectorStore(settings.chroma_persist_dir)


def get_ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline(settings=get_settings(), store=get_vector_store())


def get_retrieval_pipeline() -> RetrievalPipeline:
    return RetrievalPipeline(settings=get_settings(), store=get_vector_store())
