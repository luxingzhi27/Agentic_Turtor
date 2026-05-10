from __future__ import annotations

from typing import Protocol
import hashlib
import re

import chromadb

from app.models import NormalizedSource
from app.settings import Settings


class VectorStore(Protocol):
    def upsert_source_chunks(
        self,
        source: NormalizedSource,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> int:
        ...

    def query(self, source_id: str, query_embedding: list[float], top_k: int = 6) -> list[dict]:
        ...


class ChromaVectorStore:
    def __init__(self, settings: Settings) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))

    def upsert_source_chunks(
        self,
        source: NormalizedSource,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> int:
        if not chunks:
            return 0
        collection = self._collection_for(source.source_id)
        ids = [f"{source.source_id}-{index}" for index in range(len(chunks))]
        metadatas = [
            {
                "source_id": source.source_id,
                "source_type": source.source_type,
                "title": source.title,
                "location": f"chunk {index + 1}",
            }
            for index in range(len(chunks))
        ]
        collection.upsert(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)
        return len(chunks)

    def query(self, source_id: str, query_embedding: list[float], top_k: int = 6) -> list[dict]:
        collection = self._collection_for(source_id)
        result = collection.query(query_embeddings=[query_embedding], n_results=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {
                "document": document,
                "metadata": metadata or {},
                "distance": distance,
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]

    def _collection_for(self, source_id: str):
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", source_id)
        digest = hashlib.sha1(source_id.encode("utf-8")).hexdigest()[:8]
        name = f"source_{cleaned[:32]}_{digest}"
        return self.client.get_or_create_collection(name=name)

