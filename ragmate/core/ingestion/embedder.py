"""Embedding via Google gemini-embedding-001."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from google import genai
from google.genai import types

from ragmate.config import Settings

log = logging.getLogger(__name__)

_MAX_RETRIES = 5
_RETRY_BASE_DELAY = 2.0
_BATCH_SIZE = 100  # Gemini embedding API max per request


def _embed_with_retry(
    client: genai.Client,
    model: str,
    contents: str | list[str],
    task_type: str,
) -> list[list[float]]:
    delay = _RETRY_BASE_DELAY
    for attempt in range(_MAX_RETRIES):
        try:
            result = client.models.embed_content(
                model=model,
                contents=contents,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            return [list(e.values) for e in result.embeddings]  # type: ignore[union-attr, arg-type]
        except Exception as exc:
            if "429" in str(exc) and attempt < _MAX_RETRIES - 1:
                log.warning("[embed] rate limited, retry %d in %.0fs", attempt + 1, delay)
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise RuntimeError("unreachable")


class Embedder:
    def __init__(self, settings: Settings) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.embedding_model

    def embed_texts(
        self,
        texts: list[str],
        on_progress: Callable[[int, int], None] | None = None,
    ) -> list[list[float]]:
        """Embed in batches of up to 100 to minimise API round-trips."""
        results: list[list[float]] = []
        total = len(texts)
        starts = list(range(0, total, _BATCH_SIZE))
        n_batches = len(starts)
        for batch_num, start in enumerate(starts, 1):
            batch = texts[start : start + _BATCH_SIZE]
            log.info(
                "[embed] batch %d/%d (chunks %d-%d of %d)",
                batch_num,
                n_batches,
                start + 1,
                min(start + _BATCH_SIZE, total),
                total,
            )
            vecs = _embed_with_retry(self._client, self._model, batch, "RETRIEVAL_DOCUMENT")
            results.extend(vecs)
            if on_progress:
                on_progress(batch_num, n_batches)
        return results

    def embed_query(self, text: str) -> list[float]:
        vecs = _embed_with_retry(self._client, self._model, text, "RETRIEVAL_QUERY")
        return vecs[0]
