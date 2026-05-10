from app.services.chunking import chunk_text


def test_chunk_text_keeps_non_empty_chunks() -> None:
    chunks = chunk_text("first paragraph\n\nsecond paragraph", max_chars=50)

    assert chunks == ["first paragraph\nsecond paragraph"]


def test_chunk_text_splits_long_paragraph() -> None:
    chunks = chunk_text("a" * 125, max_chars=50)

    assert len(chunks) == 3

