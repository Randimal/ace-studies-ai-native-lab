import io
import json
import subprocess
from types import SimpleNamespace
import pytest
from pypdf import PdfWriter
from core.documents import MAX_UPLOAD_BYTES, chunk_pages, load_text, load_upload
from core.retrieval import retrieve
from core.validation import LabError


def test_stable_chunks_and_page_metadata(notes):
    first = chunk_pages([(1, notes), (2, notes)])
    assert first == chunk_pages([(1, notes), (2, notes)])
    assert {d.metadata["page"] for d in first} == {1, 2}
    assert len({d.metadata["source_id"] for d in first}) == len(first)
    assert [d.metadata["chunk_index"] for d in first] == list(range(len(first)))
    assert len({d.metadata["document_id"] for d in first}) == 1


def test_recursive_split_preserves_paragraphs_and_lines():
    paragraph = "Evaporation changes water into vapor. " * 3
    other = "Condensation changes vapor into droplets. " * 3
    chunks = chunk_pages([(None, paragraph + "\r\n\r\n" + other)], size=200, overlap=20)
    assert [d.page_content for d in chunks] == [paragraph.strip(), other.strip()]
    short = "First line explains evaporation.\r\nSecond line explains condensation.\r\n\r\nThird paragraph discusses rainfall."
    assert load_text(short)[0].page_content == short.replace("\r\n", "\n")


def test_recursive_hard_limit_and_overlap():
    # No separators: fallback must still bound every chunk without losing text.
    text = "abcdefghijklmnopqrstuvwxyz" * 30
    chunks = chunk_pages([(1, text)], size=200, overlap=40)
    assert all(0 < len(d.page_content) <= 200 for d in chunks)
    assert chunks[0].page_content + "".join(d.page_content[40:] for d in chunks[1:]) == text
    for previous, current in zip(chunks, chunks[1:]):
        assert previous.page_content[-40:] == current.page_content[:40]


def test_configuration_identity_and_repeated_pages(notes):
    a = chunk_pages([(None, notes)], size=1200, overlap=200)
    b = chunk_pages([(None, notes)], size=1200, overlap=100)
    assert a[0].metadata["document_id"] == b[0].metadata["document_id"]
    assert a[0].metadata["source_id"] != b[0].metadata["source_id"]
    assert a[0].metadata["chunking_strategy"] == "recursive_character"
    assert a[0].metadata["length_unit"] == "characters"
    repeated = chunk_pages([(None, notes), (None, notes)])
    assert len({d.metadata["source_id"] for d in repeated}) == len(repeated)
    changed = load_text(notes + " Additional source content.")
    assert a[0].metadata["document_id"] != changed[0].metadata["document_id"]


@pytest.mark.parametrize("size,overlap", [(199, 0), (3001, 0), (200, -1), (200, 101)])
def test_invalid_chunk_configuration(notes, size, overlap):
    with pytest.raises(LabError, match="chunk size"):
        chunk_pages([(None, notes)], size=size, overlap=overlap)


def test_total_limit_applies_across_pages():
    with pytest.raises(LabError, match="100,000"):
        chunk_pages([(1, "a" * 60_000), (2, "b" * 60_000)])


def test_txt_unicode(notes):
    assert load_upload(notes.encode(), "notes.TXT") == load_text(notes)
    with pytest.raises(LabError):
        load_upload(b"\xff", "notes.txt")


@pytest.mark.parametrize("text", ["", "a" * 100_001, " " * 100, "!" * 100], ids=["empty", "oversized", "whitespace", "punctuation"])
def test_bad_text(text):
    with pytest.raises(LabError):
        load_text(text)


@pytest.mark.parametrize("data,name", [(b"x", "bad.pdf"), (b"x", "bad.exe"), (b"x" * (MAX_UPLOAD_BYTES + 1), "big.txt")], ids=["bad-pdf", "extension", "oversized"])
def test_bad_upload(data, name):
    with pytest.raises(LabError):
        load_upload(data, name)


def test_pdf_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("parser", 15)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(LabError, match="timed out"):
        load_upload(b"%PDF-", "notes.pdf")


def test_pdf_page_transfer(monkeypatch, notes):
    def worker(*args, **kwargs):
        assert "API_KEY" not in " ".join(kwargs["env"])
        assert kwargs["timeout"] == 15
        return SimpleNamespace(returncode=0, stdout=json.dumps({"pages": [notes]}).encode())
    monkeypatch.setattr(subprocess, "run", worker)
    assert load_upload(b"%PDF-", "notes.pdf")[0].metadata["page"] == 1


def test_real_pdf_extraction():
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 50 700 Td (Evaporation changes water into vapor. Condensation forms droplets. Rain returns water to the surface.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    data = io.BytesIO()
    writer.write(data)
    assert "Evaporation" in load_upload(data.getvalue(), "sample.pdf")[0].page_content


def test_retrieval_coverage_and_missing_topic(notes):
    docs = chunk_pages([(i, notes) for i in range(1, 21)])
    selected = retrieve(docs)
    assert selected[0] == docs[0] and selected[-1] == docs[-1]
    assert retrieve(docs, "classification")
    with pytest.raises(LabError, match="No source"):
        retrieve(docs, "quantum")
