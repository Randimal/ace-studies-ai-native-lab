"""Temporary attempts and deterministic marking, independent of Streamlit.

Option IDs are zero-based integers. Question IDs stay stable within one exam.
Written answers are deliberately left for a human, never scored as incorrect.
"""
import json
from uuid import uuid4


def new_attempt(exam):
    return {"exam_id": uuid4().hex, "responses": {f"q{i}": None for i in range(1, len(exam.questions) + 1)},
            "submitted": False, "grades": {}}


def grade_attempt(exam, responses):
    grades = {}
    for number, question in enumerate(exam.questions, 1):
        key = f"q{number}"
        answer = responses.get(key)
        if question.kind == "written":
            grades[key] = "manual_review" if isinstance(answer, str) and answer.strip() else "unanswered"
        elif answer is None or answer == []:
            grades[key] = "unanswered"
        elif question.kind == "single":
            grades[key] = "correct" if type(answer) is int and answer == question.answer_index else "incorrect"
        else:
            valid = isinstance(answer, list) and all(type(i) is int for i in answer)
            grades[key] = "correct" if valid and len(answer) == len(set(answer)) and set(answer) == set(question.answer_indices) else "incorrect"
    return grades


def export_responses(exam, attempt):
    """A learner backup, excluding the answer key, sources and credentials."""
    return json.dumps({"schema_version": 1, "exam_id": attempt["exam_id"],
                       "submitted": attempt["submitted"], "questions": [
        {"id": f"q{i}", "kind": q.kind, "question": q.question, "options": q.options,
         "response": attempt["responses"][f"q{i}"],
         "grade": attempt["grades"].get(f"q{i}")}
        for i, q in enumerate(exam.questions, 1)]}, ensure_ascii=False, indent=2)
