from tests.helpers import scripted_exam
import math
from types import SimpleNamespace

from langchain_core.documents import Document
from pydantic import SecretStr
import pytest

from core import semantic
from core.semantic import EmbeddingSettings, SemanticRetriever, create_embeddings
from core.validation import LabError, ExamRequest
from core.providers import ProviderSettings
from core.generation import ModelCalls
from core.graph import run_exam, Decision


def settings(provider="OpenAI", key="test-key"):
    return EmbeddingSettings(provider, semantic.EMBEDDING_MODELS[provider], SecretStr(key))


@pytest.fixture
def docs():
    return [Document(page_content="Evaporation changes liquid water into vapor with energy from the Sun.", metadata={"source_id": "water", "page": 1}),
            Document(page_content="A planet travels around a star on an orbit and reflects light.", metadata={"source_id": "space", "page": 2})]


@pytest.fixture
def fake(monkeypatch):
    events = []
    def factory(config, timeout):
        assert 0 < timeout <= 30
        def documents(texts):
            events.append(("documents", len(texts)))
            return [[1., 0.] if "Evaporation" in text else [0., 1.] for text in texts]
        def query(text):
            events.append(("query", text))
            return [1., 0.]
        return SimpleNamespace(embed_documents=documents, embed_query=query)
    monkeypatch.setattr(semantic, "create_embeddings", factory)
    return events


def test_semantic_matching_and_metadata(docs, fake):
    search = SemanticRetriever(settings())
    result = search(docs, "liquid becoming gas", limit=1)
    assert result[0].metadata == {"source_id": "water", "page": 1}
    assert search.calls == 2


def test_cache_reuse_invalidation_and_no_credentials(docs, fake):
    cache = {}
    SemanticRetriever(settings(), cache)(docs, "gas")
    second = SemanticRetriever(settings(), cache)
    second(docs, "gas")
    assert second.calls == 1 and second.cache_hit
    assert "test-key" not in repr(cache)
    changed = SemanticRetriever(settings(key="other-key"), cache)
    changed(docs, "gas")
    assert changed.calls == 2
    changed_docs = [docs[0].model_copy(update={"page_content": "Evaporation is another description"}), docs[1]]
    assert SemanticRetriever(settings(key="other-key"), cache)(changed_docs, "gas")
    assert sum(event[0] == "documents" for event in fake) == 3


def test_blank_query_never_calls_api(docs, fake):
    search = SemanticRetriever(settings())
    assert search(docs, "")
    assert search.calls == 0 and not fake


def test_prepare_then_search_without_reembedding(docs, fake):
    cache = {}
    SemanticRetriever(settings(), cache).prepare(docs)
    assert fake == [("documents", 2)]
    search = SemanticRetriever(settings(), cache, prepared_only=True)
    assert search(docs, "")
    assert fake == [("documents", 2)]
    assert search(docs, "gas")
    assert search(docs, "water")
    assert fake == [("documents", 2), ("query", "gas"), ("query", "water")]


def test_prepared_search_cannot_rebuild_missing_index(docs, fake):
    with pytest.raises(LabError, match="prepared index is unavailable"):
        SemanticRetriever(settings(), {}, prepared_only=True)(docs, "gas")
    assert not fake


def test_session_caches_separate(docs, fake):
    a, b = {}, {}
    SemanticRetriever(settings(), a)(docs, "gas")
    SemanticRetriever(settings(), b)(docs, "gas")
    assert a["store"] is not b["store"]


@pytest.mark.parametrize("provider", ["OpenAI", "Google Gemini", "OpenRouter"])
def test_real_embedding_client_bounds(provider):
    client = create_embeddings(settings(provider), 3)
    if provider in {"OpenAI", "OpenRouter"}:
        assert client.max_retries == 0 and client.request_timeout == 3
        assert client.check_embedding_ctx_length is False
        assert client.model_kwargs["encoding_format"] == "float"
        if provider == "OpenRouter":
            assert client.openai_api_base == "https://openrouter.ai/api/v1"
    else:
        config = client._build_config(task_type="RETRIEVAL_QUERY")
        assert config.http_options.timeout == 3000
        assert config.http_options.retry_options.attempts == 1
        assert client.vertexai is False


def test_errors_redacted(monkeypatch, docs):
    def fail(*args):
        raise RuntimeError("private-document secret-key")
    monkeypatch.setattr(semantic, "create_embeddings", fail)
    with pytest.raises(LabError) as error:
        SemanticRetriever(settings())(docs, "gas")
    assert "secret-key" not in str(error.value) and "private-document" not in str(error.value)


@pytest.mark.parametrize("vector", [[math.nan, 1.], [0., 0.], []])
def test_invalid_vectors_rejected(monkeypatch, docs, vector):
    monkeypatch.setattr(semantic, "create_embeddings", lambda *a: SimpleNamespace(embed_documents=lambda texts: [vector for _ in texts]))
    with pytest.raises(LabError):
        SemanticRetriever(settings())(docs, "gas")


def test_budget_deadline_and_batching(docs, fake):
    search = SemanticRetriever(settings())
    search.calls = 32
    with pytest.raises(LabError) as error:
        search(docs, "gas")
    assert error.value.code == "embedding_limit"
    search = SemanticRetriever(settings())
    search.deadline = 0
    with pytest.raises(LabError) as error:
        search(docs, "gas")
    assert error.value.code == "timeout"
    many = [Document(page_content="Evaporation " * 90, metadata={"source_id": str(i)}) for i in range(20)]
    search = SemanticRetriever(settings())
    search(many, "gas")
    assert search.calls == 4


@pytest.mark.parametrize("workflow", ["deterministic", "agentic"])
def test_both_graphs_use_semantic_retrieval(monkeypatch, docs, fake, workflow):
    choices = iter(["retrieve", "generate", "validate", "finish"])
    def invoke(self, schema, *a, **k):
        if schema is Decision:
            action = next(choices)
            return Decision(action=action, query="liquid becoming gas" if action == "retrieve" else "")
        return scripted_exam(ExamRequest(count=1), docs)
    monkeypatch.setattr(ModelCalls, "invoke", invoke)
    search = SemanticRetriever(settings())
    result = run_exam(ExamRequest(count=1, topic="liquid becoming gas", workflow=workflow), docs,
                      ProviderSettings("Groq", "test-model", SecretStr("generation-key")), semantic=search)
    assert result["retrieval"] == "semantic" and result["embedding_calls"] == 2
    assert result["sources"][0].metadata["source_id"] == "water"


def test_saved_index_resumes_without_reembedding_documents(tmp_path, docs, fake):
    first = SemanticRetriever(settings(), persistent=True, database_path=tmp_path)
    first(docs, "gas")
    name = first.cache["store"].name
    resumed = SemanticRetriever(settings(), persistent=True, resume_id=name, database_path=tmp_path)
    resumed(docs, "gas")
    assert resumed.calls == 1 and resumed.cache_hit
    assert sum(event[0] == "documents" for event in fake) == 1
    resumed.cache["store"].delete()


def test_memory_collection_deleted_on_rebuild(docs, fake):
    cache = {}
    SemanticRetriever(settings(), cache)(docs, "gas")
    previous = cache["store"]
    name = previous.name
    SemanticRetriever(settings(key="different"), cache)(docs, "gas")
    with pytest.raises(Exception):
        previous.client.get_collection(name, embedding_function=None)
    cache["store"].delete()


def test_recursive_chunks_round_trip_and_config_invalidation(fake, tmp_path):
    from core.documents import chunk_pages
    source = [(1, "Evaporation changes liquid water into vapor. " * 12)]
    docs = chunk_pages(source, size=200, overlap=40)
    search = SemanticRetriever(settings(), persistent=True, database_path=tmp_path)
    try:
        result = search(docs, "vapor")
        originals = {d.metadata["source_id"]: d for d in docs}
        assert result and all(d == originals[d.metadata["source_id"]] for d in result)
        changed = chunk_pages(source, size=200, overlap=20)
        resumed = SemanticRetriever(settings(), persistent=True, database_path=tmp_path,
                                    resume_id=search.cache["store"].name)
        with pytest.raises(LabError, match="does not match"):
            resumed(changed, "vapor")
    finally:
        search.cache["store"].delete()
