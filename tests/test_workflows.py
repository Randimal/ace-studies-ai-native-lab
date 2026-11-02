import pytest
from pydantic import SecretStr
from core.documents import load_text
from core.generation import Limits, ModelCalls
from tests.helpers import scripted_exam
from core.graph import Decision, run_exam
from core.providers import ProviderSettings
from core.validation import Exam, ExamRequest, LabError, Question


def settings():
    return ProviderSettings("Groq", "test-model", SecretStr("private-test-key"))


def test_llm_end_to_end(monkeypatch, notes):
    from types import SimpleNamespace
    from langchain_core.messages import AIMessage
    from core import generation
    docs = load_text(notes)
    exam = scripted_exam(ExamRequest(count=5), docs)
    monkeypatch.setattr(generation, "create_model", lambda *a: SimpleNamespace(
        invoke=lambda *a, **k: AIMessage(content=exam.model_dump_json())))
    result = run_exam(ExamRequest(count=5), docs, settings())
    assert len(result["exam"].questions) == 5
    assert result["trace"] == ["prepare", "retrieve", "generate", "validate", "finish"]
    assert result["model_calls"] == 1


def test_empty_input_rejected():
    with pytest.raises(LabError) as error:
        run_exam(ExamRequest(), [], settings())
    assert error.value.code == "input"


def test_topic_only(monkeypatch):
    exam = Exam(questions=[Question(question="Which number is even?", options=["1", "2", "3", "5"], answer_index=1, explanation="Two is divisible by two.")])
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: exam)
    result = run_exam(ExamRequest(count=1, topic="numbers"), [], settings())
    assert result["basis"] == "model knowledge" and "retrieve" not in result["trace"]


def test_retry_then_success(monkeypatch, notes):
    docs = load_text(notes)
    responses = iter([Exam(), scripted_exam(ExamRequest(count=1), docs)])
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: next(responses))
    result = run_exam(ExamRequest(count=1), docs, settings())
    assert result["trace"].count("generate") == 2


def test_retry_exhaustion(monkeypatch, notes):
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: Exam())
    with pytest.raises(LabError) as failure:
        run_exam(ExamRequest(count=1), load_text(notes), settings(), Limits(max_attempts=2))
    assert failure.value.code == "retry_limit"


def test_insufficient_evidence_stops(monkeypatch, notes):
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: Exam(status="insufficient_evidence"))
    with pytest.raises(LabError) as failure:
        run_exam(ExamRequest(count=1), load_text(notes), settings())
    assert failure.value.code == "insufficient_evidence"


def test_agent_routing_and_premature_finish(monkeypatch, notes):
    docs = load_text(notes)
    choices = iter(["finish", "retrieve", "generate", "validate", "finish"])
    def invoke(self, schema, *args, **kwargs):
        return Decision(action=next(choices)) if schema is Decision else scripted_exam(ExamRequest(count=1), docs)
    monkeypatch.setattr(ModelCalls, "invoke", invoke)
    result = run_exam(ExamRequest(count=1, workflow="agentic"), docs, settings())
    assert result["trace"].count("decide") == 5
    assert result["trace"][-1] == "finish"
    assert "private-test-key" not in str(result)


def test_agent_revise(monkeypatch, notes):
    docs = load_text(notes)
    choices = iter(["retrieve", "generate", "revise", "validate", "finish"])
    def invoke(self, schema, *args, **kwargs):
        return Decision(action=next(choices)) if schema is Decision else scripted_exam(ExamRequest(count=1), docs)
    monkeypatch.setattr(ModelCalls, "invoke", invoke)
    result = run_exam(ExamRequest(count=1, workflow="agentic"), docs, settings())
    assert "revise" in result["trace"]


def test_agent_decision_bound(monkeypatch, notes):
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: Decision(action="finish"))
    with pytest.raises(LabError) as failure:
        run_exam(ExamRequest(workflow="agentic"), load_text(notes), settings(), Limits(max_decisions=2))
    assert failure.value.code == "decision_limit"


def test_deadline_rejects_late_result(monkeypatch, notes):
    import core.generation as module
    now = [0]
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    def late(*args, **kwargs):
        now[0] = 121
        return scripted_exam(ExamRequest(count=1), load_text(notes))
    monkeypatch.setattr(ModelCalls, "invoke", late)
    with pytest.raises(LabError) as failure:
        run_exam(ExamRequest(count=1), load_text(notes), settings())
    assert failure.value.code == "timeout"
