import json

import pytest
from pydantic import ValidationError

from core.attempts import export_responses, grade_attempt, new_attempt
from core.documents import load_text
from core.export import export_html
from tests.helpers import scripted_exam
from core.validation import ExamRequest, Question, validate_exam, LabError


def mixed_exam(notes):
    documents = load_text(notes)
    request = ExamRequest(count=3, question_format="mixed")
    exam = scripted_exam(request, documents)
    return validate_exam(exam, request, {d.metadata["source_id"] for d in documents}, True)


def test_marking_and_backup(notes):
    exam = mixed_exam(notes)
    attempt = new_attempt(exam)
    attempt["responses"] = {"q1": exam.questions[0].answer_index,
                            "q2": exam.questions[1].answer_indices[::-1], "q3": "My answer"}
    assert grade_attempt(exam, attempt["responses"]) == {
        "q1": "correct", "q2": "correct", "q3": "manual_review"}
    assert grade_attempt(exam, {"q2": [0, 1, 2]}) == {
        "q1": "unanswered", "q2": "incorrect", "q3": "unanswered"}
    assert grade_attempt(exam, {"q2": [0], "q3": "  "})["q2"] == "incorrect"
    backup = json.loads(export_responses(exam, attempt))
    assert backup["questions"][2]["response"] == "My answer"
    assert not {"rubric", "explanation", "answer_index", "answer_indices", "source_ids"} & backup["questions"][0].keys()
    assert new_attempt(exam)["exam_id"] != attempt["exam_id"]


@pytest.mark.parametrize("fields", [
    {"kind": "written"},
    {"kind": "written", "rubric": "Review", "options": ["a", "b", "c", "d"]},
    {"kind": "multiple", "options": ["a", "b", "c", "d"], "answer_indices": [0]},
    {"kind": "multiple", "options": ["a", "b", "c", "d"], "answer_indices": [0, 0]},
    {"kind": "multiple", "options": ["a", "b", "c", "d"], "answer_indices": [0, 4]},
])
def test_invalid_question_contract(fields):
    with pytest.raises(ValidationError):
        Question(question="Question", explanation="Reason", **fields)


def test_mixed_exports_and_type_validation(notes):
    exam = mixed_exam(notes)
    paper, key = export_html(exam), export_html(exam, answer_key=True)
    assert "Select all correct answers" in paper and "Write a short answer" in paper
    assert exam.questions[2].rubric not in paper
    assert exam.questions[2].rubric.replace('"', '&quot;') in key
    with pytest.raises(LabError):
        validate_exam(exam, ExamRequest(count=3), set(), False)


@pytest.mark.parametrize("kind", ["single", "multiple", "written", "mixed"])
def test_all_question_contracts_at_maximum_count(monkeypatch, notes, kind):
    from types import SimpleNamespace
    from langchain_core.messages import AIMessage
    from pydantic import SecretStr
    from core import generation
    from core.generation import ModelCalls, Limits, generate
    from core.providers import ProviderSettings
    request = ExamRequest(count=10, question_format=kind)
    docs = load_text(notes)
    response = scripted_exam(request, docs)
    def invoke(messages, **kwargs):
        payload = json.loads(messages[-1].content.split("\n", 1)[1])
        assert payload["question_types"] == request.question_types()
        return AIMessage(content=response.model_dump_json())
    monkeypatch.setattr(generation, "create_model", lambda *a: SimpleNamespace(invoke=invoke))
    calls = ModelCalls(ProviderSettings("OpenAI", "test-model", SecretStr("test-key")), Limits())
    exam = generate(calls, request, docs)
    validate_exam(exam, request, {d.metadata["source_id"] for d in docs}, True)
    assert calls.calls == 1
