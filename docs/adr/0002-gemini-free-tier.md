# ADR 0002: Gemini 2.5 Flash + gemini-embedding-001 for LLM and embeddings

**Status:** Accepted
**Date:** 2025-06-07

## Context

RAG requires two model calls per query: one for embeddings (document indexing and query embedding) and one for answer generation. Both must be affordable at zero cost during development and light production use.

Alternatives considered:
- **OpenAI** (gpt-4o + text-embedding-3-small): paid from the first token, no free tier for embedding.
- **Ollama** (local models): no API key, but requires local GPU or slow CPU inference; not portable for demos.
- **Google AI free tier** (Gemini 2.5 Flash + gemini-embedding-001): generous free quota, no credit card required for basic use.

## Decision

Use `gemini-2.5-flash` for answer generation and `models/gemini-embedding-001` for all embedding operations via the `google-genai` Python SDK.

## Consequences

**Good:**
- Zero cost for development and low-traffic demos.
- Both models accessible via a single SDK and a single API key.
- `gemini-embedding-001` produces 768-dimensional vectors well-suited for cosine similarity search.
- Batched embedding (up to 100 texts per API call) keeps ingestion fast.

**Bad:**
- Rate limits on the free tier (requests-per-minute) may cause throttling under heavy load.
- Vendor lock-in to Google AI; switching LLMs requires changing the `Generator` and `Embedder` classes.

**Neutral:**
- The `Embedder` and `Generator` classes are thin wrappers, making a provider swap straightforward if needed.
