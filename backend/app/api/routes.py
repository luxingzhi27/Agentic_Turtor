from __future__ import annotations

import platform

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.adapters.document_loader import DocumentLoader, DocumentLoaderError
from app.adapters.llm import (
    LLMConfigurationError,
    LLMResponseError,
    OpenAICompatibleEmbeddingClient,
    OpenAICompatibleLLMClient,
)
from app.adapters.vector_store import ChromaVectorStore
from app.models import (
    AnalysisResponse,
    GapsRequest,
    GapsResponse,
    HealthResponse,
    NormalizedSource,
    NudgesRequest,
    NudgesResponse,
    TraceIndexResponse,
)
from app.services.examples import get_demo_page, get_example_bundle, get_example_content, list_examples
from app.services.gap_detector import GapDetector
from app.services.nudge_engine import NudgeEngine
from app.services.trace_indexer import TraceIndexer
from app.settings import get_settings


router = APIRouter(prefix="/api")


def services() -> tuple[DocumentLoader, TraceIndexer, GapDetector, NudgeEngine]:
    settings = get_settings()
    llm = OpenAICompatibleLLMClient(settings)
    embedding = OpenAICompatibleEmbeddingClient(settings)
    vector_store = ChromaVectorStore(settings)
    return DocumentLoader(), TraceIndexer(llm, embedding, vector_store), GapDetector(), NudgeEngine(llm)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return HealthResponse(
        status="ok",
        llm_configured=settings.llm_configured,
        embedding_configured=settings.embedding_configured,
        chroma_dir=str(settings.chroma_dir),
        python_runtime=platform.python_version(),
    )


@router.get("/examples")
async def examples():
    return list_examples()


@router.get("/examples/{example_id}")
async def example_content(example_id: str):
    try:
        title, content = get_example_content(example_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Example not found.") from exc
    return {"example_id": example_id, "title": title, "content": content}


@router.get("/examples/{example_id}/bundle")
async def example_bundle(example_id: str):
    try:
        return get_example_bundle(example_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Example not found.") from exc


@router.get("/demo-pages/{example_id}")
async def demo_page(example_id: str):
    try:
        return get_demo_page(example_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Demo page not found.") from exc


@router.post("/sources/parse", response_model=NormalizedSource)
async def parse_source(
    source_type: str = Form(...),
    text: str | None = Form(None),
    url: str | None = Form(None),
    example_id: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> NormalizedSource:
    loader, _indexer, _gap_detector, _nudge_engine = services()
    try:
        if source_type == "text":
            return await loader.from_text(text or "")
        if source_type == "auto":
            payload = None
            if file is not None:
                payload = (file.filename or "upload", file.content_type, await file.read())
            return await loader.from_mixed(text=text, file_payload=payload)
        if source_type == "file":
            if file is None:
                raise DocumentLoaderError("No file was uploaded.")
            return await loader.from_file(file.filename or "upload", file.content_type, await file.read())
        if source_type == "url":
            if not url:
                raise DocumentLoaderError("URL input is empty.")
            return await loader.from_url(url)
        if source_type == "example":
            if not example_id:
                raise DocumentLoaderError("Example id is missing.")
            title, content = get_example_content(example_id)
            return loader.from_example(example_id, title, content)
    except DocumentLoaderError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    raise HTTPException(status_code=422, detail="Unsupported source type.")


@router.post("/traces/index", response_model=TraceIndexResponse)
async def index_trace(source: NormalizedSource) -> TraceIndexResponse:
    _loader, indexer, _gap_detector, _nudge_engine = services()
    try:
        return await indexer.index(source)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (LLMResponseError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/gaps/detect", response_model=GapsResponse)
async def detect_gaps(request: GapsRequest) -> GapsResponse:
    _loader, _indexer, gap_detector, _nudge_engine = services()
    return gap_detector.detect(request.concept_index, request.learning_events)


@router.post("/nudges/generate", response_model=NudgesResponse)
async def generate_nudges(request: NudgesRequest) -> NudgesResponse:
    _loader, _indexer, _gap_detector, nudge_engine = services()
    return await nudge_engine.generate(request.gaps)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    source_type: str = Form(...),
    text: str | None = Form(None),
    url: str | None = Form(None),
    example_id: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> AnalysisResponse:
    source = await parse_source(source_type=source_type, text=text, url=url, example_id=example_id, file=file)
    trace_index = await index_trace(source)
    gaps = await detect_gaps(
        GapsRequest(concept_index=trace_index.concept_index, learning_events=trace_index.learning_events)
    )
    nudges = await generate_nudges(NudgesRequest(gaps=gaps.gaps))
    return AnalysisResponse(trace_index=trace_index, gaps=gaps.gaps, nudges=nudges.nudges)
