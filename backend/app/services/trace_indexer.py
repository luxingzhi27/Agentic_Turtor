from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from pydantic import ValidationError

from app.adapters.llm import EmbeddingClient, LLMClient
from app.adapters.vector_store import VectorStore
from app.models import (
    ConceptStats,
    Evidence,
    LLMExtractionEnvelope,
    LearningEvent,
    NormalizedSource,
    TraceIndexResponse,
)
from app.services.chunking import chunk_text


TRACE_EXTRACTION_SYSTEM_PROMPT = """You are the Trace Indexer for an action-oriented tutor.
Extract a student's learning trace from unstructured materials.
Return only a JSON object with this exact top-level shape:
{"learning_events": [ ... ]}

Each learning event must include:
- event_id: short stable id
- timestamp: ISO datetime or null
- type: one of exercise, note, error, feedback, reflection, resource, unknown
- concepts: array of concise concepts
- summary: one sentence describing what happened
- performance: object with score, confidence, attempts, each 0-1 or null except attempts integer/null
- errors: array of repeated mistakes or misconceptions
- evidence: array of {source_id, quote, location}
- extraction_confidence: number from 0 to 1

Do not explain concepts. Do not solve problems. Preserve uncertainty with null values and confidence scores."""


def build_user_prompt(source: NormalizedSource, evidence_chunks: list[dict]) -> str:
    evidence_text = "\n\n".join(
        f"[{index + 1}] {item['metadata'].get('location', 'chunk')}\n{item['document'][:900]}"
        for index, item in enumerate(evidence_chunks)
    )
    if not evidence_text:
        evidence_text = source.raw_content[:6000]
    return f"""Source id: {source.source_id}
Title: {source.title}
Source type: {source.source_type}

Evidence chunks:
{evidence_text}

Extract at least three learning events when the source supports it. Use source_id "{source.source_id}" in evidence entries."""


class TraceIndexer:
    def __init__(
        self,
        llm_client: LLMClient,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
    ) -> None:
        self.llm_client = llm_client
        self.embedding_client = embedding_client
        self.vector_store = vector_store

    async def index(self, source: NormalizedSource) -> TraceIndexResponse:
        chunks = chunk_text(source.raw_content)
        chunk_embeddings = await self.embedding_client.embed(chunks)
        chunks_indexed = self.vector_store.upsert_source_chunks(source, chunks, chunk_embeddings)
        query = f"{source.title}\nlearning errors mistakes concepts confidence score practice review decay avoided"
        query_embeddings = await self.embedding_client.embed([query])
        if not query_embeddings:
            raise ValueError("Embedding API returned no query embedding.")
        query_embedding = query_embeddings[0]
        evidence_chunks = self.vector_store.query(source.source_id, query_embedding, top_k=min(4, len(chunks)))
        extraction = await self.llm_client.extract_json(
            TRACE_EXTRACTION_SYSTEM_PROMPT,
            build_user_prompt(source, evidence_chunks),
        )
        try:
            envelope = LLMExtractionEnvelope.model_validate(extraction)
        except ValidationError as exc:
            raise ValueError(f"LLM extraction failed schema validation: {exc}") from exc
        events = self._normalize_events(envelope.learning_events, source)
        return TraceIndexResponse(
            source=source,
            chunks_indexed=chunks_indexed,
            learning_events=events,
            concept_index=self._build_concept_index(events),
        )

    def _normalize_events(self, events: list[LearningEvent], source: NormalizedSource) -> list[LearningEvent]:
        normalized: list[LearningEvent] = []
        for index, event in enumerate(events, start=1):
            if not event.event_id:
                event.event_id = f"{source.source_id}_event_{index}"
            if not event.evidence:
                event.evidence = [
                    Evidence(
                        source_id=source.source_id,
                        quote=event.summary[:220],
                        location="LLM summary",
                    )
                ]
            normalized.append(event)
        return normalized

    def _build_concept_index(self, events: list[LearningEvent]) -> dict[str, ConceptStats]:
        grouped: dict[str, list[LearningEvent]] = defaultdict(list)
        for event in events:
            for concept in event.concepts:
                grouped[concept.lower()].append(event)

        index: dict[str, ConceptStats] = {}
        for concept, concept_events in grouped.items():
            scores = [event.performance.score for event in concept_events if event.performance.score is not None]
            confidences = [
                event.performance.confidence
                for event in concept_events
                if event.performance.confidence is not None
            ]
            timestamps = [event.timestamp for event in concept_events if event.timestamp is not None]
            errors = Counter(error for event in concept_events for error in event.errors)
            evidence_sources = []
            for event in concept_events:
                for evidence in event.evidence:
                    if evidence.location:
                        evidence_sources.append(f"{evidence.source_id}:{evidence.location}")
                    else:
                        evidence_sources.append(evidence.source_id)
            index[concept] = ConceptStats(
                events=len(concept_events),
                last_seen=max(timestamps) if timestamps else None,
                average_score=round(mean(scores), 3) if scores else None,
                average_confidence=round(mean(confidences), 3) if confidences else None,
                common_errors=[error for error, _count in errors.most_common(5)],
                evidence_sources=list(dict.fromkeys(evidence_sources))[:8],
                summaries=[event.summary for event in concept_events[:5]],
            )
        return index
