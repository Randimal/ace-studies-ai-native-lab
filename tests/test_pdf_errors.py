"""Specific, content-free PDF failure messages across the subprocess boundary."""
import io
import json
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter

from core.documents import load_upload, PDF_ERRORS
from core.pdf_worker import extract
from core.validation import LabError


@pytest.mark.parametrize("code", list(PDF_ERRORS))
def test_worker_error_is_explained(monkeypatch, code):
    monkeypatch.setattr("core.documents.subprocess.run", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout=json.dumps({"error": code}).encode(), stderr=b"Debugger warning"))
    with pytest.raises(LabError) as error:
        load_upload(b"%PDF-", "notes.pdf")
    assert str(error.value) == PDF_ERRORS[code]


@pytest.mark.parametrize("kind,code", [("encrypted", "encrypted"), ("long", "page_limit"), ("blank", "no_text")])
def test_real_pdf_worker_failures(kind, code):
    writer = PdfWriter()
    for _ in range(51 if kind == "long" else 1):
        writer.add_blank_page(width=100, height=100)
    if kind == "encrypted":
        writer.encrypt("synthetic-password")
    data = io.BytesIO()
    writer.write(data)
    with pytest.raises(LabError) as error:
        load_upload(data.getvalue(), "test.pdf")
    assert str(error.value) == PDF_ERRORS[code]


def test_tolerant_parser_and_text_limit(monkeypatch):
    def reader(*args, **kwargs):
        assert kwargs["strict"] is False
        return SimpleNamespace(is_encrypted=False, pages=[SimpleNamespace(extract_text=lambda: "x" * 100_001)])
    monkeypatch.setattr("pypdf.PdfReader", reader)
    assert extract(b"%PDF-") == {"error": "text_limit"}


def test_parser_exception_details_not_exposed(monkeypatch):
    def reader(*args, **kwargs):
        raise ValueError("PRIVATE DOCUMENT CONTENT")
    monkeypatch.setattr("pypdf.PdfReader", reader)
    assert extract(b"%PDF-") == {"error": "parse_error"}


@pytest.mark.parametrize("stdout,returncode", [(b"invalid", 0), (b"[]", 0),
    (b'{"pages": [42]}', 0), (b'{"error": "PRIVATE"}', 0), (b"", 1)])
def test_invalid_worker_response_is_safe(monkeypatch, stdout, returncode):
    monkeypatch.setattr("core.documents.subprocess.run", lambda *a, **k: SimpleNamespace(
        returncode=returncode, stdout=stdout, stderr=b"PRIVATE"))
    with pytest.raises(LabError) as error:
        load_upload(b"%PDF-", "notes.pdf")
    assert "PRIVATE" not in str(error.value)
