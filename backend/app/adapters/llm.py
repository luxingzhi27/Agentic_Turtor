from __future__ import annotations

import json
import re
from typing import Protocol

import httpx

from app.settings import Settings


class LLMClient(Protocol):
    async def extract_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...

    async def rewrite(self, system_prompt: str, user_prompt: str) -> str:
        ...


class EmbeddingClient(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class LLMConfigurationError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


class OpenAICompatibleLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        if not self.settings.llm_api_key:
            raise LLMConfigurationError("LLM_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

    async def extract_json(self, system_prompt: str, user_prompt: str) -> dict:
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        content = await self._chat(payload)
        return self._parse_json_object(content)

    async def rewrite(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        return await self._chat(payload)

    async def _chat(self, payload: dict) -> str:
        url = self._endpoint(self.settings.llm_base_url, "chat/completions")
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
        except httpx.RequestError as exc:
            raise LLMResponseError(f"LLM API request failed: {exc}") from exc
        if response.status_code >= 400:
            raise LLMResponseError(f"LLM API returned {response.status_code}: {response.text[:500]}")
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError("LLM response did not include choices[0].message.content.") from exc

    def _parse_json_object(self, content: str) -> dict:
        cleaned = content.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
        if fenced:
            cleaned = fenced.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMResponseError("LLM returned invalid JSON.") from exc

    def _endpoint(self, base_url: str, suffix: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith(suffix):
            return normalized
        return f"{normalized}/{suffix}"


class OpenAICompatibleEmbeddingClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        if not self.settings.embedding_api_key:
            raise LLMConfigurationError("EMBEDDING_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {self.settings.embedding_api_key}",
            "Content-Type": "application/json",
        }

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.settings.embedding_model:
            raise LLMConfigurationError("EMBEDDING_MODEL is not configured.")
        url = self._endpoint(self.settings.embedding_base_url, "embeddings")
        payload = {"model": self.settings.embedding_model, "input": texts}
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
        except httpx.RequestError as exc:
            raise LLMResponseError(f"Embedding API request failed: {exc}") from exc
        if response.status_code >= 400:
            raise LLMResponseError(f"Embedding API returned {response.status_code}: {response.text[:500]}")
        data = response.json()
        try:
            return [item["embedding"] for item in sorted(data["data"], key=lambda item: item["index"])]
        except (KeyError, TypeError) as exc:
            raise LLMResponseError("Embedding response did not include data[].embedding.") from exc

    def _endpoint(self, base_url: str, suffix: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith(suffix):
            return normalized
        return f"{normalized}/{suffix}"
