"""Structural checks establish consistency and traceability, not factual truth."""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LabError(Exception):
    """Only fixed, content-free messages may cross the UI boundary."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)


class ExamRequest(StrictModel):
    count: int = Field(default=5, ge=1, le=10)
    difficulty: Literal["Easy", "Medium", "Hard", "Mixed"] = "Medium"
    topic: str = Field(default="", max_length=200)
    workflow: Literal["deterministic", "agentic"] = "deterministic"
    question_format: Literal["single", "multiple", "written", "mixed"] = "single"
    practice_topics: list[str] = Field(default_factory=list, max_length=10)
    previous_questions: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def valid_practice_plan(self):
        if any(len(q) > 1200 for q in self.previous_questions):
            raise ValueError("Previous questions exceed the length limit")
        if self.practice_topics and (len(self.practice_topics) != self.count or
                any(not t.strip() or len(t) > 100 for t in self.practice_topics)):
            raise ValueError("Practice topics must contain one bounded topic per question")
        return self

    def question_types(self):
        """Mixed cycles through the three types in a predictable order."""
        types = ["single", "multiple", "written"]
        return [types[i % 3] if self.question_format == "mixed" else self.question_format
                for i in range(self.count)]


def normalized(value: str) -> str:
    return " ".join(re.findall(r"\w+", value.casefold()))


class Question(StrictModel):
    topic: str = Field(default="", max_length=100)
    learning_objective: str = Field(default="", max_length=300)
    kind: Literal["single", "multiple", "written"] = "single"
    question: str = Field(min_length=1, max_length=1200)
    options: list[str] = Field(default_factory=list, max_length=4)
    answer_index: int | None = Field(default=None, ge=0, le=3)
    answer_indices: list[int] = Field(default_factory=list, max_length=4)
    rubric: str = Field(default="", max_length=3000)
    explanation: str = Field(min_length=1, max_length=3000)
    source_ids: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def distinct_options(self):
        keys = [normalized(option) for option in self.options]
        if self.kind != "written" and (any(not key for key in keys) or len(set(keys)) != 4):
            raise ValueError("Four distinct nonempty options are required")
        if any(len(option) > 1200 for option in self.options):
            raise ValueError("Option too long")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("Duplicate source references")
        if self.kind == "single" and (self.answer_index is None or self.answer_indices or self.rubric):
            raise ValueError("Single-answer questions require only answer_index")
        if self.kind == "multiple" and (self.answer_index is not None or self.rubric
                or not 2 <= len(self.answer_indices) <= 4
                or len(set(self.answer_indices)) != len(self.answer_indices)
                or any(i < 0 or i > 3 for i in self.answer_indices)):
            raise ValueError("Multiple-answer questions require two to four distinct answer_indices")
        if self.kind == "written" and (self.options or self.answer_index is not None
                or self.answer_indices or not self.rubric):
            raise ValueError("Written questions require a rubric and no options or answer indices")
        return self


class Exam(StrictModel):
    status: Literal["ok", "insufficient_evidence"] = "ok"
    questions: list[Question] = Field(default_factory=list, max_length=10)


def validate_exam(exam: Exam, request: ExamRequest, source_ids: set[str], grounded: bool) -> Exam:
    if exam.status == "insufficient_evidence":
        raise LabError("insufficient_evidence", "Not enough supported material for this exam. Add notes, broaden the topic, or request fewer questions.")
    if len(exam.questions) != request.count:
        raise LabError("invalid_output", "The generated exam did not match the requested question count.")
    seen = set()
    if [q.kind for q in exam.questions] != request.question_types():
        raise LabError("invalid_output", "The generated question types did not match the requested format.")
    for index, question in enumerate(exam.questions):
        if request.practice_topics and (question.topic != request.practice_topics[index]
                                        or not question.learning_objective):
            raise LabError("invalid_output", "Questions must match the practice topics and include learning objectives.")
        key = normalized(question.question)
        if not key or key in seen:
            raise LabError("invalid_output", "The generated exam contains empty or duplicate questions.")
        seen.add(key)
        if key in {normalized(q) for q in request.previous_questions}:
            raise LabError("invalid_output", "The generated exam repeats a recent question.")
        if grounded and (not question.source_ids or not set(question.source_ids) <= source_ids):
            raise LabError("invalid_output", "The generated exam contains missing or unsupported source references.")
        if not grounded and question.source_ids:
            raise LabError("invalid_output", "Topic-only exams must not invent document references.")
    return exam
