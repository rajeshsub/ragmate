"""Unit tests for the recursive character chunker."""

from ragmate.core.ingestion.chunker import split_text


def test_short_text_returns_single_chunk() -> None:
    text = "Hello world"
    chunks = split_text(text, chunk_size=512, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_empty_text_returns_empty_list() -> None:
    chunks = split_text("", chunk_size=512, chunk_overlap=50)
    assert chunks == []


def test_long_text_splits_into_multiple_chunks() -> None:
    # ~4000 chars → should produce multiple 512-token chunks
    text = ("word " * 800).strip()
    chunks = split_text(text, chunk_size=512, chunk_overlap=50)
    assert len(chunks) > 1


def test_chunks_cover_all_content() -> None:
    text = "paragraph one.\n\nparagraph two.\n\nparagraph three."
    chunks = split_text(text, chunk_size=10, chunk_overlap=2)
    reconstructed = " ".join(chunks)
    # All original words must appear somewhere in chunks
    for word in ["paragraph", "one", "two", "three"]:
        assert word in reconstructed


def test_whitespace_only_filtered() -> None:
    text = "   \n\n   "
    chunks = split_text(text, chunk_size=512, chunk_overlap=50)
    assert chunks == []


def test_chunk_size_respected() -> None:
    text = "a" * 10000
    chunks = split_text(text, chunk_size=100, chunk_overlap=10)
    # Each chunk should be roughly <= 100 tokens (100*4=400 chars + some tolerance)
    for chunk in chunks:
        assert len(chunk) <= 500  # generous bound given approximate token count
