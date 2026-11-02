"""Synthetic model responses for tests, not a question-generation feature."""
from core.validation import Exam, Question


def scripted_exam(request, sources):
    questions = []
    for i, kind in enumerate(request.question_types(), 1):
        fields = {"kind": kind, "question": f"Synthetic test question {i}",
                  "explanation": "Synthetic test explanation.",
                  "source_ids": [sources[0].metadata["source_id"]] if sources else []}
        if kind == "written":
            fields["rubric"] = "Check the written response against the source."
        else:
            fields["options"] = ["Alpha", "Beta", "Gamma", "Delta"]
            fields["answer_index" if kind == "single" else "answer_indices"] = 0 if kind == "single" else [0, 1]
        questions.append(Question(**fields))
    return Exam(questions=questions)
