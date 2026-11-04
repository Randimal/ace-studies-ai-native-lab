"""Exercise OpenRouter through the real SDK with an in-process HTTP stub."""
import json

import httpx2 as httpx  # Transport used by the pinned OpenAI SDK.
from pydantic import SecretStr

from core.config import load_defaults
from core.providers import ProviderSettings, create_model
from core.semantic import EmbeddingSettings, SemanticRetriever
from langchain_core.documents import Document


def test_openrouter_wire_protocol_and_key_isolation(monkeypatch):
    requests = []
    def send(client, request, **kwargs):
        body = json.loads(request.content)
        requests.append((str(request.url), body))
        assert request.headers["authorization"] == "Bearer router-test-key"
        if request.url.path.endswith("/embeddings"):
            assert body["model"] == "nvidia/nemotron-3-embed-1b:free"
            assert body["encoding_format"] == "float"
            assert all(isinstance(item, str) for item in body["input"])
            payload = {"data": [{"embedding": [1., 0.], "index": i, "object": "embedding"}
                                for i, _ in enumerate(body["input"])], "model": body["model"],
                       "object": "list", "usage": {"prompt_tokens": 1, "total_tokens": 1}}
        else:
            assert request.url.path == "/api/v1/chat/completions"
            assert body["model"] == "openrouter/free"
            payload = {"id": "test", "object": "chat.completion", "created": 0, "model": body["model"],
                       "choices": [{"index": 0, "finish_reason": "stop", "message": {
                           "role": "assistant", "content": '{"status":"insufficient_evidence","questions":[]}'}}]}
        return httpx.Response(200, request=request, json=payload)
    monkeypatch.setattr(httpx.Client, "send", send)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    key = SecretStr("router-test-key")
    model = create_model(ProviderSettings("OpenRouter", "openrouter/free", key), 5, 100)
    assert json.loads(model.invoke("Generate").content)["status"] == "insufficient_evidence"
    cache = {}
    docs = [Document(page_content="Introductory machine learning", metadata={"source_id": "s1"})]
    settings = EmbeddingSettings("OpenRouter", "nvidia/nemotron-3-embed-1b:free", key)
    SemanticRetriever(settings, cache).prepare(docs)
    assert SemanticRetriever(settings, cache, prepared_only=True)(docs, "learning")
    assert [url for url, _ in requests] == ["https://openrouter.ai/api/v1/chat/completions",
        "https://openrouter.ai/api/v1/embeddings", "https://openrouter.ai/api/v1/embeddings"]


def test_openrouter_defaults_and_ui(monkeypatch, tmp_path):
    from core import config
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    path = tmp_path / ".env"
    path.write_text("LLM_PROVIDER=OpenRouter\nLLM_MODEL=openrouter/free\n"
                    "EMBEDDING_PROVIDER=OpenRouter\nRETRIEVAL_MODE=semantic\n"
                    "OPENROUTER_API_KEY=router-test-key\n", encoding="utf-8")
    defaults = load_defaults(path, {})
    assert defaults.key("OpenRouter") == "router-test-key"
    assert defaults.embedding_model == "nvidia/nemotron-3-embed-1b:free"
    assert "router-test-key" not in repr(defaults)
    monkeypatch.setattr(config, "ENV_FILE", path)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.selectbox(key="provider").value == "OpenRouter"
    assert app.selectbox(key="embedding_provider").value == "OpenRouter"
    assert app.text_input(key="key_OpenRouter").value == ""
    assert app.checkbox(key="reuse_embedding_key").value
    assert app.text_input(key="embedding_model_OpenRouter").value == defaults.embedding_model
