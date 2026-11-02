import pytest
from core.study_session import prepare_material
from core.validation import LabError


def test_multi_upload_and_deduplication(notes):
    files = [("first.txt", notes.encode()), ("duplicate.txt", notes.encode()),
             ("second.txt", (notes + " Additional notes about rainfall.").encode())]
    material = prepare_material("Upload PDF / TXT", uploads=files)
    assert material["names"] == ["first.txt", "second.txt"]
    chunks = material["documents"]
    assert len({d.metadata["document_id"] for d in chunks}) == 2
    assert len({d.metadata["source_id"] for d in chunks}) == len(chunks)
    assert {d.metadata["source_name"] for d in chunks} == {"first.txt", "second.txt"}


def test_combined_upload_limits(notes):
    for files in ([], [(str(i)+".txt", notes.encode()) for i in range(11)],
                  [("huge.txt", b"x" * (10 * 1024 * 1024 + 1))],
                  [("a.txt", b"a" * 60_000), ("b.txt", b"b" * 60_000)]):
        with pytest.raises(LabError):
            prepare_material("Upload PDF / TXT", uploads=files)


def test_topic_session_needs_no_document():
    assert prepare_material("Topic only")["documents"] == []
