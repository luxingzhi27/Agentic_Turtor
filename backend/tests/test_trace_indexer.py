from datetime import datetime, timezone

import pytest

from app.models import NormalizedSource, SourceMetadata
from app.services.trace_indexer import TraceIndexer


class FakeLLM:
    async def extract_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "learning_events": [
                {
                    "event_id": "e1",
                    "timestamp": "2026-04-20",
                    "type": "exercise",
                    "concepts": ["Recursion", "Base Case"],
                    "summary": "The student failed recursion tasks because the base case was missing.",
                    "performance": {"score": 0.45, "confidence": 0.35, "attempts": 3},
                    "errors": ["missing base case"],
                    "evidence": [{"source_id": "source_1", "quote": "forgot the base case", "location": "chunk 1"}],
                    "extraction_confidence": 0.9,
                }
            ]
        }

    async def rewrite(self, system_prompt: str, user_prompt: str) -> str:
        return "Write a small attempt and mark the stuck point."

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(index + 1)] * 4 for index, _text in enumerate(texts)]


class FakeVectorStore:
    def __init__(self) -> None:
        self.chunks: list[str] = []

    def upsert_source_chunks(self, source: NormalizedSource, chunks: list[str], embeddings: list[list[float]]) -> int:
        self.chunks = chunks
        return len(chunks)

    def query(self, source_id: str, query_embedding: list[float], top_k: int = 6) -> list[dict]:
        return [
            {
                "document": chunk,
                "metadata": {"source_id": source_id, "location": f"chunk {index + 1}"},
                "distance": 0.1,
            }
            for index, chunk in enumerate(self.chunks[:top_k])
        ]


@pytest.mark.anyio
async def test_trace_indexer_builds_concept_index() -> None:
    source = NormalizedSource(
        source_id="source_1",
        source_type="text",
        title="Recursion notes",
        raw_content="I forgot the base case during recursion practice.",
        metadata=SourceMetadata(captured_at=datetime.now(timezone.utc), parser="test"),
    )

    response = await TraceIndexer(FakeLLM(), FakeLLM(), FakeVectorStore()).index(source)

    assert response.chunks_indexed == 1
    assert response.learning_events[0].timestamp is not None
    assert "recursion" in response.concept_index
    assert response.concept_index["recursion"].average_score == 0.45

