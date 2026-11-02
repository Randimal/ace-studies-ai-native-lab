"""Bounded input loading; LangChain Documents carry stable chunk/page metadata."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .validation import LabError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_CHARS = 100_000
MAX_PAGES = 50
PDF_TIMEOUT = 15
PDF_ERRORS = {
    "encrypted": "This PDF is encrypted or password-protected. Export an unencrypted copy and upload it again.",
    "page_limit": "This PDF exceeds the 50-page limit. Upload a smaller chapter or page range.",
    "text_limit": "This PDF exceeds 100,000 extracted characters. Split it into smaller documents and prepare a smaller collection.",
    "no_text": "No readable text was extracted from this PDF. It may be scanned or blank. Use an OCR tool or upload a text-based PDF/TXT.",
    "upload_limit": "This PDF exceeds the 10 MiB upload limit. Upload a smaller file.",
    "parse_error": "This PDF could not be parsed. Try opening it in a PDF reader and exporting a new copy, or upload its text as TXT.",
}


def chunk_pages(pages: list[tuple[int | None, str]], size: int = 1200, overlap: int = 200) -> list[Document]:
    if not 200 <= size <= 3000 or not 0 <= overlap <= size // 2:
        raise LabError("input", "Invalid chunk size or overlap.")
    # Keep paragraph/line boundaries: the recursive splitter uses these before
    # falling back to spaces and individual characters. Sizes are characters.
    normalized_pages, total = [], 0
    for page, raw in pages:
        text = unicodedata.normalize("NFKC", raw).replace("\r\n", "\n").replace("\r", "\n")
        text = "".join(c if c == "\n" or not unicodedata.category(c).startswith("C") else " " for c in text)
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        total += len(text)
        if total > MAX_CHARS:
            raise LabError("input", "Documents may contain at most 100,000 extracted characters.")
        normalized_pages.append((page, text))
    if total < 60 or not any(any(c.isalnum() for c in text) for _, text in normalized_pages):
        raise LabError("input", "Provide at least 60 characters of readable study material. Scanned PDFs need OCR, which is not included.")

    document_id = hashlib.sha256(json.dumps(normalized_pages, ensure_ascii=False).encode()).hexdigest()
    config = {"chunking_strategy": "recursive_character", "chunking_version": 1,
              "chunk_size": size, "chunk_overlap": overlap, "length_unit": "characters"}
    # Recursive chunking: try paragraph breaks, then line breaks, then spaces,
    # and finally individual characters until each chunk fits the size limit.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap, length_function=len,
        separators=["\n\n", "\n", " ", ""], is_separator_regex=False,
    )
    chunks = []
    # Split each page separately to retain unambiguous page citations. The same
    # records feed lexical and vector retrieval; source_id is their shared ID.
    for page, text in normalized_pages:
        for content in splitter.split_text(text):
            chunk_index = len(chunks)
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            identity = json.dumps([document_id, config, chunk_index, content_hash], sort_keys=True)
            identifier = hashlib.sha256(identity.encode()).hexdigest()[:24]
            chunks.append(Document(page_content=content, metadata={
                "source_id": f"chunk-{identifier}", "document_id": document_id,
                "page": page, "chunk_index": chunk_index, "content_hash": content_hash, **config,
            }))
    return chunks


def load_text(text: str) -> list[Document]:
    print(len(text))
    if len(text) > MAX_CHARS:
        raise LabError("input", "Notes may contain at most 100,000 characters.")
    return chunk_pages([(None, text)])


def load_upload(data: bytes, filename: str) -> list[Document]:
    if len(data) > MAX_UPLOAD_BYTES:
        raise LabError("input", "Uploads must be at most 10 MiB.")
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        try:
            return load_text(data.decode("utf-8-sig"))
        except UnicodeDecodeError:
            raise LabError("input", "Save the TXT file as UTF-8 and try again.") from None
    if suffix != ".pdf" or not data.startswith(b"%PDF-"):
        raise LabError("input", "Upload a UTF-8 TXT file or a text-based PDF.")
    # Input travels over pipes, never through a saved user document. A separate
    # process lets us kill a stuck parser; a thread timeout would leave it running.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "core.pdf_worker"], input=data,
            capture_output=True, timeout=PDF_TIMEOUT,
            cwd=Path(__file__).resolve().parents[1],
            env={k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TMP", "TEMP"}},
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode:
            raise LabError("input", "The PDF extraction process stopped unexpectedly. Try a smaller PDF or upload its text as TXT.")
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError()
        if payload.get("error"):
            code = payload["error"]
            message = PDF_ERRORS.get(code, PDF_ERRORS["parse_error"]) if isinstance(code, str) else PDF_ERRORS["parse_error"]
            raise LabError("input", message)
        pages = payload["pages"]
        if not isinstance(pages, list) or any(not isinstance(page, str) for page in pages):
            raise ValueError()
        if len(pages) > MAX_PAGES:
            raise LabError("input", PDF_ERRORS["page_limit"])
        return chunk_pages([(index, page) for index, page in enumerate(pages, 1)])
    except subprocess.TimeoutExpired:
        raise LabError("input", "PDF extraction timed out. Try a smaller document.") from None
    except (ValueError, KeyError, OSError):
        raise LabError("input", "The PDF worker could not return valid extraction data. Check your Python environment or try a different PDF/TXT file.") from None
