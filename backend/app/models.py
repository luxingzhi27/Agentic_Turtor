from __future__ import annotations

from datetime import datetime, time
from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


SourceType = Literal["text", "file", "url", "example", "auto"]
LearningEventType = Literal["exercise", "note", "error", "feedback", "reflection", "resource", "unknown"]
GapType = Literal["weak", "avoided", "decaying"]


class SourceMetadata(BaseModel):
    url: str | None = None
    filename: str | None = None
    captured_at: datetime
    content_type: str | None = None
    parser: str


class NormalizedSource(BaseModel):
    source_id: str
    source_type: SourceType
    title: str
    raw_content: str
    metadata: SourceMetadata


class Evidence(BaseModel):
    source_id: str
    quote: str
    location: str | None = None


class Performance(BaseModel):
    score: float | None = Field(default=None, ge=0, le=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    attempts: int | None = Field(default=None, ge=0)


class LearningEvent(BaseModel):
    event_id: str
    timestamp: datetime | None = None
    type: LearningEventType = "unknown"
    concepts: list[str] = Field(default_factory=list)
    summary: str
    performance: Performance = Field(default_factory=Performance)
    errors: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    extraction_confidence: float = Field(default=0.5, ge=0, le=1)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_date_only_timestamp(cls, value: object) -> object:
        if isinstance(value, str) and len(value) == 10:
            try:
                return datetime.combine(datetime.fromisoformat(value).date(), time.min)
            except ValueError:
                return value
        return value

    @field_validator("concepts", "errors")
    @classmethod
    def strip_blank_strings(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]


class ConceptStats(BaseModel):
    events: int
    last_seen: datetime | None = None
    average_score: float | None = None
    average_confidence: float | None = None
    common_errors: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)
    summaries: list[str] = Field(default_factory=list)


class TraceIndexResponse(BaseModel):
    source: NormalizedSource
    chunks_indexed: int
    learning_events: list[LearningEvent]
    concept_index: dict[str, ConceptStats]


class Gap(BaseModel):
    concept: str
    gap_type: GapType
    severity: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)
    calculation_notes: list[str] = Field(default_factory=list)


class GapsRequest(BaseModel):
    concept_index: dict[str, ConceptStats]
    learning_events: list[LearningEvent] = Field(default_factory=list)


class GapsResponse(BaseModel):
    gaps: list[Gap]


class Nudge(BaseModel):
    concept: str
    gap_type: GapType
    nudge: str
    action_type: str
    exercise_title: str | None = None
    practice_prompt: str | None = None
    practice_materials: list[str] = Field(default_factory=list)
    practice_steps: list[str] = Field(default_factory=list)
    submission_checklist: list[str] = Field(default_factory=list)
    encouragement: str
    priority: Literal["low", "medium", "high"]
    passed_guardrail: bool


class NudgesRequest(BaseModel):
    gaps: list[Gap]


class NudgesResponse(BaseModel):
    nudges: list[Nudge]


class AnalysisResponse(BaseModel):
    trace_index: TraceIndexResponse
    gaps: list[Gap]
    nudges: list[Nudge]


class ExampleInfo(BaseModel):
    example_id: str
    title: str
    description: str


class ExampleBundle(BaseModel):
    example_id: str
    title: str
    content: str
    file_name: str
    file_content: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    llm_configured: bool
    embedding_configured: bool
    chroma_dir: str
    python_runtime: str


class LLMExtractionEnvelope(BaseModel):
    learning_events: list[LearningEvent]


class LLMChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMChatRequest(BaseModel):
    messages: list[LLMChatMessage]
    response_format: dict[str, Any] | None = None


class URLParseRequest(BaseModel):
    url: HttpUrl
