import pytest

from core.adaptive import plan_practice, record_submission, topic_map
from core.attempts import new_attempt, grade_attempt
from core.validation import ExamRequest, LabError, validate_exam
from tests.helpers import scripted_exam


def test_allocation_and_low_evidence():
    topics = ["Probability", "Algebra", "Calculus"]
    profile = {"Probability": dict(correct=0, incorrect=1, unanswered=0),
               "Algebra": dict(correct=4, incorrect=0, unanswered=0)}
    plan, reason = plan_practice(topics, profile, 5, True)
    assert plan == ["Probability"] * 3 + ["Calculus", "Algebra"]
    assert "not a diagnosis" in reason
    assert plan_practice(topics, {}, 3, True)[0] == topics
    for count in range(1, 11):
        assert len(plan_practice(topics, profile, count, True)[0]) == count


def test_submission_is_once_and_ignores_written():
    exam = scripted_exam(ExamRequest(count=3, question_format="mixed"), [])
    for q in exam.questions:
        q.topic = "Probability"
    attempt = new_attempt(exam)
    profile = {}
    record_submission(profile, exam, attempt, ["Probability"])
    assert profile == {}
    attempt["responses"] = {"q1": 1, "q2": [], "q3": "answer"}
    attempt["grades"] = grade_attempt(exam, attempt["responses"])
    attempt["submitted"] = True
    record_submission(profile, exam, attempt, ["Probability"])
    record_submission(profile, exam, attempt, ["Probability"])
    assert profile == {"Probability": dict(correct=0, incorrect=1, unanswered=1)}


def test_topic_contract_and_repetition():
    request = ExamRequest(count=1, practice_topics=["Probability"])
    exam = scripted_exam(request, [])
    with pytest.raises(LabError):
        validate_exam(exam, request, set(), False)
    exam.questions[0].topic = "Probability"
    exam.questions[0].learning_objective = "Calculate conditional probability"
    validate_exam(exam, request, set(), False)
    request.previous_questions = [exam.questions[0].question]
    with pytest.raises(LabError, match="repeats"):
        validate_exam(exam, request, set(), False)
    with pytest.raises(LabError):
        topic_map("Probability\nprobability")


def test_targeted_retrieval_uses_each_planned_topic(monkeypatch):
    from core import graph
    from core.generation import ModelCalls
    from core.providers import ProviderSettings
    from langchain_core.documents import Document
    from pydantic import SecretStr
    queries = []
    docs = [Document(page_content="Study evidence", metadata={"source_id": "s1"})]
    def retrieve(documents, query, **kwargs):
        queries.append((query, kwargs["byte_budget"]))
        return docs
    def invoke(self, schema, instruction, data, *args):
        exam = scripted_exam(ExamRequest(count=3), docs)
        for q, topic in zip(exam.questions, data["practice_topics"]):
            q.topic, q.learning_objective = topic, "Apply this concept"
        return exam
    monkeypatch.setattr(graph, "retrieve", retrieve)
    monkeypatch.setattr(ModelCalls, "invoke", invoke)
    result = graph.run_exam(ExamRequest(count=3, practice_topics=["Probability", "Probability", "Algebra"]),
                            docs, ProviderSettings("OpenAI", "test", SecretStr("test")))
    assert queries == [("Probability", 8000), ("Algebra", 8000)]
    assert len(result["sources"]) == 1


def test_ui_adaptive_followup_and_clear(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from core.generation import ModelCalls
    from pathlib import Path
    plans = []
    def invoke(self, schema, instruction, data, *args):
        plans.append(data["practice_topics"])
        request = ExamRequest(count=data["count"])
        exam = scripted_exam(request, [])
        for i, q in enumerate(exam.questions):
            q.topic = data["practice_topics"][i]
            q.learning_objective = "Apply " + q.topic
            q.question = f"Paper {len(plans)} question {i}"
        return exam
    monkeypatch.setattr(ModelCalls, "invoke", invoke)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=30).run()
    app.text_input(key="model_OpenAI").set_value("test-model")
    app.text_input(key="key_OpenAI").set_value("test-key")
    app.radio(key="source_mode").set_value("Topic only").run()
    app.button(key="prepare_material").click().run()
    app.text_input(key="topic").set_value("Math")
    app.text_area(key="learning_topics_text").set_value("Probability\nAlgebra\nCalculus")
    app.checkbox(key="consent").check()
    app.button(key="generate_exam").click().run()
    assert not app.error and not app.exception
    attempt_id = app.session_state["attempt"]["exam_id"]
    app.radio(key=f"response_{attempt_id}_q1").set_value(1).run()
    app.button(key="submit_exam").click().run()
    assert app.session_state["learning_profile"]["Probability"]["incorrect"] == 1
    app.checkbox(key="adaptive_mode").check()
    app.button(key="generate_exam").click().run()
    assert not app.error and not app.exception
    assert plans[-1][:3] == ["Probability"] * 3
    assert app.session_state["learning_profile"]["Probability"]["incorrect"] == 1
    app.button(key="clear_session").click().run()
    assert "learning_profile" not in app.session_state
