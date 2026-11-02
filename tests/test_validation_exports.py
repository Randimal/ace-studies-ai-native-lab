import pytest
from pydantic import ValidationError
from core.export import export_html
from core.validation import Exam, ExamRequest, LabError, Question, validate_exam


def question(**changes):
    fields = dict(question="Choose a planet", options=["Earth", "Sun", "Moon", "Comet"], answer_index=0,
                  explanation="TEACHER_ONLY_REASON", source_ids=["chunk-one"])
    fields.update(changes)
    return Question(**fields)


@pytest.mark.parametrize("changes", [{"options": ["a", "b", "c"]}, {"options": ["a", "A", "b", "c"]},
                                     {"answer_index": 4}, {"explanation": " "}, {"question": ""}])
def test_bad_mcq(changes):
    with pytest.raises(ValidationError):
        question(**changes)


def test_count_duplicates_and_citations():
    for exam, request, sources, grounded in [
        (Exam(questions=[question()]), ExamRequest(count=2), {"chunk-one"}, True),
        (Exam(questions=[question(), question()]), ExamRequest(count=2), {"chunk-one"}, True),
        (Exam(questions=[question()]), ExamRequest(count=1), {"chunk-other"}, True),
        (Exam(questions=[question()]), ExamRequest(count=1), set(), False),
    ]:
        with pytest.raises(LabError):
            validate_exam(exam, request, sources, grounded)


def test_export_separation_and_escape():
    exam = Exam(questions=[question(question='<script>alert("bad")</script>')])
    paper = export_html(exam)
    key = export_html(exam, answer_key=True)
    assert "<script>" not in paper and "&lt;script&gt;" in paper
    assert "TEACHER_ONLY_REASON" not in paper
    assert "answer_index" not in paper and "chunk-one" not in paper
    assert "TEACHER_ONLY_REASON" in key and "chunk-one" in key
