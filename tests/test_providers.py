import os
from types import SimpleNamespace

from langchain_core.messages import AIMessage
import pytest
from pydantic import SecretStr

from core import generation
from core.generation import Limits, ModelCalls
from core.providers import ProviderSettings, create_model
from core.validation import Exam, LabError


@pytest.mark.parametrize("provider", ["OpenAI", "Groq", "Anthropic", "Google Gemini", "OpenRouter"])
def test_real_client_construction_no_network(provider):
    settings = ProviderSettings(provider, "test-model", SecretStr("synthetic-test-key"))
    model = create_model(settings, 4, 100)
    assert model.max_retries == 0
    assert "synthetic-test-key" not in repr(settings)
    assert model.cache is False
    if provider == "OpenRouter":
        assert model.openai_api_base == "https://openrouter.ai/api/v1"
        assert model.use_responses_api is False


@pytest.mark.parametrize("provider,model,key", [("Other", "x", "key"), ("Demo", "x", "key"), ("Groq", "", "key"), ("Groq", "x", "")])
def test_bad_configuration(provider, model, key):
    with pytest.raises(LabError):
        ProviderSettings(provider, model, SecretStr(key))


def test_credentials_are_per_invocation(monkeypatch):
    keys = []
    before = dict(os.environ)
    def factory(settings, *args):
        keys.append(settings.api_key.get_secret_value())
        return SimpleNamespace(invoke=lambda *a, **k: AIMessage(content='{"status":"insufficient_evidence","questions":[]}'))
    monkeypatch.setattr(generation, "create_model", factory)
    for key in ("session-one", "session-two"):
        ModelCalls(ProviderSettings("Groq", "model", SecretStr(key)), Limits()).invoke(Exam, "Exam", {})
    assert keys == ["session-one", "session-two"]
    assert dict(os.environ) == before


def test_provider_error_redaction(monkeypatch, caplog):
    def factory(*args):
        raise RuntimeError("secret-key and PRIVATE_DOCUMENT")
    monkeypatch.setattr(generation, "create_model", factory)
    calls = ModelCalls(ProviderSettings("Groq", "model", SecretStr("secret-key")), Limits())
    with pytest.raises(LabError) as failure:
        calls.invoke(Exam, "Exam", {"notes": "PRIVATE_DOCUMENT"})
    assert "secret-key" not in str(failure.value) + caplog.text
    assert "PRIVATE_DOCUMENT" not in str(failure.value) + caplog.text


@pytest.mark.parametrize("content", ['{"status":"ok","questions":', 'not JSON'])
def test_incomplete_json_rejected(monkeypatch, content):
    monkeypatch.setattr(generation, "create_model", lambda *a: SimpleNamespace(invoke=lambda *a, **k: AIMessage(content=content)))
    calls = ModelCalls(ProviderSettings("Groq", "model", SecretStr("key")), Limits())
    with pytest.raises(LabError) as failure:
        calls.invoke(Exam, "Exam", {})
    assert failure.value.code == "invalid_output"


def test_call_and_token_limits(monkeypatch):
    monkeypatch.setattr(generation, "create_model", lambda *a: SimpleNamespace(invoke=lambda *a, **k: AIMessage(content='{"status":"ok","questions":[]}')))
    settings = ProviderSettings("Groq", "model", SecretStr("key"))
    calls = ModelCalls(settings, Limits(max_calls=1))
    calls.invoke(Exam, "Exam", {})
    with pytest.raises(LabError) as failure:
        calls.invoke(Exam, "Exam", {})
    assert failure.value.code == "call_limit"
    with pytest.raises(LabError) as failure:
        ModelCalls(settings, Limits(token_budget=1)).invoke(Exam, "Exam", {})
    assert failure.value.code == "token_limit"


def test_tracing_disabled_even_when_inherited(monkeypatch):
    from langsmith.run_helpers import get_tracing_context
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    def invoke(*args, **kwargs):
        assert get_tracing_context()["enabled"] is False
        return AIMessage(content='{"status":"ok","questions":[]}')
    monkeypatch.setattr(generation, "create_model", lambda *a: SimpleNamespace(invoke=invoke))
    ModelCalls(ProviderSettings("Groq", "model", SecretStr("key")), Limits()).invoke(Exam, "Exam", {})


def test_reported_token_overrun(monkeypatch):
    response = AIMessage(content='{"status":"ok","questions":[]}',
                         usage_metadata={"input_tokens": 100001, "output_tokens": 1, "total_tokens": 100002})
    monkeypatch.setattr(generation, "create_model", lambda *a: SimpleNamespace(invoke=lambda *a, **k: response))
    with pytest.raises(LabError) as failure:
        ModelCalls(ProviderSettings("Groq", "model", SecretStr("key")), Limits()).invoke(Exam, "Exam", {})
    assert failure.value.code == "token_limit"
