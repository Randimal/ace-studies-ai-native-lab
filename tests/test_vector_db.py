import json
import subprocess
import sys

from langchain_core.documents import Document
import pytest

from core.vector_db import ChromaIndex, clear_index
from core.validation import LabError


def documents():
    return [Document(page_content="water document", metadata={"source_id": "water", "page": None}),
            Document(page_content="space document", metadata={"source_id": "space", "page": 4})]


def test_actual_chroma_cosine_and_metadata():
    index = ChromaIndex()
    try:
        index.build(documents(), [[1., 0.], [0., 1.]], "test-fingerprint")
        assert index.collection.configuration["hnsw"]["space"] == "cosine"
        result = index.search([0., 3.], 2)
        assert result[0].metadata == {"source_id": "space", "page": 4}
        assert result[1].metadata["page"] is None
        assert result[0].page_content == "space document"
        assert index.client.get_settings().anonymized_telemetry is False
    finally:
        index.delete()


def test_collections_are_isolated_and_clear_deletes():
    a, b = ChromaIndex(), ChromaIndex()
    a.build(documents(), [[1., 0.], [0., 1.]], "a")
    b.build(documents(), [[1., 0.], [0., 1.]], "b")
    assert a.name != b.name
    old_name = a.name
    cache = {"store": a}
    clear_index(cache)
    assert not cache
    with pytest.raises(Exception):
        a.client.get_collection(old_name, embedding_function=None)
    assert b.collection.count() == 2
    b.delete()


def test_persistence_resume_and_explicit_delete(tmp_path):
    index = ChromaIndex(persistent=True, path=tmp_path)
    index.build(documents(), [[1., 0.], [0., 1.]], "identity")
    name = index.name
    clear_index({"store": index})
    restored = ChromaIndex(persistent=True, path=tmp_path)
    restored.restore(name, "identity")
    assert restored.search([1., 0.], 1)[0].metadata["source_id"] == "water"
    assert set(restored.collection.metadata) == {"identity", "dimension"}
    clear_index({"store": restored}, delete_saved=True)
    with pytest.raises(LabError):
        ChromaIndex(persistent=True, path=tmp_path).restore(name, "identity")


def test_saved_index_mismatch_does_not_expose_contents(tmp_path):
    index = ChromaIndex(persistent=True, path=tmp_path)
    index.build(documents(), [[1., 0.], [0., 1.]], "original")
    try:
        other = ChromaIndex(persistent=True, path=tmp_path)
        with pytest.raises(LabError) as error:
            other.restore(index.name, "different")
        assert "water document" not in str(error.value)
        assert other.collection is None
    finally:
        index.delete()


@pytest.mark.parametrize("name", ["../../private", "", "ace-foo", "other-" + "a" * 32])
def test_bad_resume_id(tmp_path, name):
    with pytest.raises(LabError):
        ChromaIndex(persistent=True, path=tmp_path).restore(name, "identity")


def test_resume_across_process_restart(tmp_path):
    # Real embedded database persistence, without an embedding API or server.
    code = '''
import sys
from core.vector_db import ChromaIndex
from langchain_core.documents import Document
index = ChromaIndex(persistent=True, path=sys.argv[1])
index.build([Document(page_content="synthetic", metadata={"source_id":"one","page":None})], [[1.,0.]], "identity")
print(index.name)
'''
    result = subprocess.run([sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, "Chroma subprocess failed"
    name = result.stdout.strip().splitlines()[-1]
    restored = ChromaIndex(persistent=True, path=tmp_path)
    restored.restore(name, "identity")
    assert restored.collection.count() == 1
    restored.delete()
