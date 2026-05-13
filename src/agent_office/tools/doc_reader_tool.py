import os
import tempfile
from pathlib import Path

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

_SUPPORTED = {".pdf", ".docx", ".txt", ".md", ".csv"}
_TEXT_TYPES = {".txt", ".md", ".csv"}


class DocReaderInput(BaseModel):
    source: str = Field(description="Local file path or URL to the document (PDF, DOCX, TXT, MD, CSV)")


class DocReaderTool(BaseTool):
    name: str = "document_reader"
    description: str = (
        "Read and extract full text content from a document. "
        "Accepts a local file path or an HTTP/HTTPS URL. "
        "Supported formats: PDF, DOCX, TXT, MD, CSV."
    )
    args_schema: type[BaseModel] = DocReaderInput

    def _run(self, source: str) -> str:
        if source.startswith("http://") or source.startswith("https://"):
            return self._from_url(source)
        return self._from_path(Path(source))

    def _from_url(self, url: str) -> str:
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        suffix = Path(url.split("?")[0]).suffix.lower() or ".tmp"

        # Plain-text formats don't need the disk round-trip
        if suffix in _TEXT_TYPES:
            return resp.text

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(resp.content)
            tmp = f.name
        try:
            return self._from_path(Path(tmp))
        finally:
            os.unlink(tmp)

    def _from_path(self, path: Path) -> str:
        if not path.exists():
            return f"Error: file not found — {path}"

        suffix = path.suffix.lower()
        if suffix not in _SUPPORTED:
            return f"Unsupported file type '{suffix}'. Supported: {', '.join(sorted(_SUPPORTED))}"

        if suffix == ".pdf":
            return self._read_pdf(path)
        if suffix == ".docx":
            return self._read_docx(path)
        return path.read_text(encoding="utf-8", errors="replace")

    def _read_pdf(self, path: Path) -> str:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(p.strip() for p in pages if p.strip())

    def _read_docx(self, path: Path) -> str:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
