"""Answer generation via Gemini 2.0 Flash."""

from __future__ import annotations

import time

from google import genai
from google.genai import types

from ragmate.config import Settings

_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based strictly on the provided context.
If the answer cannot be found in the context, say so clearly rather than making something up.
Always cite the source document when answering."""

_PROMPT_TEMPLATE = """Context:
{context}

Question: {question}

Answer based only on the context above:"""

_MAX_RETRIES = 5
_RETRY_BASE_DELAY = 2.0


class Generator:
    def __init__(self, settings: Settings) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    def generate(self, question: str, context_chunks: list[dict[str, str]]) -> str:
        context = "\n\n---\n\n".join(
            f"[Source: {c.get('doc_id', 'unknown')}]\n{c['text']}" for c in context_chunks
        )
        prompt = _PROMPT_TEMPLATE.format(context=context, question=question)
        delay = _RETRY_BASE_DELAY
        for attempt in range(_MAX_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
                )
                return str(response.text)
            except Exception as exc:
                if "429" in str(exc) and attempt < _MAX_RETRIES - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
        raise RuntimeError("unreachable")
