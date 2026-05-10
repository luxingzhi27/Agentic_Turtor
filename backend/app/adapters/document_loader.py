from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import csv
import io
import re

from bs4 import BeautifulSoup
import httpx
from pypdf import PdfReader

from app.models import NormalizedSource, SourceMetadata


class DocumentLoaderError(RuntimeError):
    pass


class DocumentLoader:
    async def from_mixed(
        self,
        text: str | None = None,
        file_payload: tuple[str, str | None, bytes] | None = None,
    ) -> NormalizedSource:
        parts: list[str] = []
        title_parts: list[str] = []
        parsers: list[str] = []

        text = (text or "").strip()
        urls = self._extract_urls(text)
        text_without_standalone_urls = text
        for url in urls:
            text_without_standalone_urls = text_without_standalone_urls.replace(url, "").strip()

        if text_without_standalone_urls:
            parts.append(f"[Typed notes]\n{text_without_standalone_urls}")
            title_parts.append("Typed notes")
            parsers.append("plain-text")

        for url in urls:
            try:
                url_source = await self.from_url(url)
                parts.append(f"[Linked material: {url_source.title}]\n{url_source.raw_content}")
                title_parts.append(url_source.title)
                parsers.append("beautifulsoup")
            except DocumentLoaderError as exc:
                parts.append(f"[Linked material unavailable: {url}]\n{exc}")
                title_parts.append("Unavailable link")
                parsers.append("url-error")

        if file_payload is not None:
            filename, content_type, content = file_payload
            file_source = await self.from_file(filename, content_type, content)
            parts.append(f"[Uploaded file: {file_source.title}]\n{file_source.raw_content}")
            title_parts.append(file_source.title)
            parsers.append(file_source.metadata.parser)

        if not parts:
            raise DocumentLoaderError("Add text, a URL, or a supported file before analyzing.")

        source = self._source(
            "text",
            " + ".join(title_parts[:3]) or "Mixed learning materials",
            "\n\n".join(parts),
            parser="+".join(dict.fromkeys(parsers)) or "mixed",
        )
        source.source_id = f"mixed_{uuid4().hex[:10]}"
        return source

    async def from_text(self, text: str, title: str = "Pasted learning trace") -> NormalizedSource:
        content = text.strip()
        if not content:
            raise DocumentLoaderError("Text input is empty.")
        return self._source("text", title, content, parser="plain-text")

    async def from_file(self, filename: str, content_type: str | None, content: bytes) -> NormalizedSource:
        suffix = Path(filename).suffix.lower()
        if suffix in {".txt", ".md"}:
            text = content.decode("utf-8", errors="replace")
            parser = "utf-8-text"
        elif suffix == ".csv":
            text = self._csv_to_text(content)
            parser = "csv"
        elif suffix == ".pdf":
            text = self._pdf_to_text(content)
            parser = "pypdf"
        else:
            raise DocumentLoaderError("Unsupported file type. Use .txt, .md, .csv, or .pdf.")
        if not text.strip():
            raise DocumentLoaderError("No text could be extracted from the file.")
        source = self._source("file", filename, text, parser=parser)
        source.metadata.filename = filename
        source.metadata.content_type = content_type
        return source

    async def from_url(self, url: str) -> NormalizedSource:
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": "ActionTutorPrototype/0.1"})
            response.raise_for_status()
        except Exception as exc:
            raise DocumentLoaderError("Could not fetch the URL. Paste the page text as a fallback.") from exc
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        if not text:
            raise DocumentLoaderError("The URL did not contain readable text. Paste the page text as a fallback.")
        source = self._source("url", title, text, parser="beautifulsoup")
        source.metadata.url = url
        source.metadata.content_type = response.headers.get("content-type")
        return source

    def from_example(self, example_id: str, title: str, content: str) -> NormalizedSource:
        source = self._source("example", title, content, parser="example-loader")
        source.source_id = f"example_{example_id}"
        return source

    def _source(self, source_type: str, title: str, raw_content: str, parser: str) -> NormalizedSource:
        return NormalizedSource(
            source_id=f"{source_type}_{uuid4().hex[:10]}",
            source_type=source_type,
            title=title,
            raw_content=raw_content.strip(),
            metadata=SourceMetadata(
                captured_at=datetime.now(timezone.utc),
                parser=parser,
            ),
        )

    def _csv_to_text(self, content: bytes) -> str:
        text = content.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        lines = [" | ".join(cell.strip() for cell in row) for row in reader]
        return "\n".join(lines)

    def _pdf_to_text(self, content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for index, page in enumerate(reader.pages):
            extracted = page.extract_text() or ""
            if extracted.strip():
                pages.append(f"[page {index + 1}]\n{extracted.strip()}")
        return "\n\n".join(pages)

    def _extract_urls(self, text: str) -> list[str]:
        matches = re.findall(r"https?://[^\s<>\"]+", text)
        return [match.rstrip(".,);]") for match in dict.fromkeys(matches)]
