"""Explainable session-only practice planning; no model or database calls."""
from .validation import LabError


def topic_map(text):
    """A learner-reviewed vocabulary avoids model-generated topic synonyms."""
    topics = list(dict.fromkeys(line.strip() for line in text.splitlines() if line.strip()))
    if len(topics) > 20 or any(len(t) > 100 for t in topics):
        raise LabError("input", "Use at most 20 topics, each at most 100 characters.")
    if len({t.casefold() for t in topics}) != len(topics):
        raise LabError("input", "Topic names must be distinct, ignoring capitalization.")
    return topics


def record_submission(profile, exam, attempt, topics):
    """Count each submitted paper once; keep totals after history eviction."""
    if not attempt["submitted"] or attempt.get("performance_recorded"):
        return
    for index, question in enumerate(exam.questions, 1):
        if question.topic not in topics:
            continue
        stats = profile.setdefault(question.topic, dict(correct=0, incorrect=0, unanswered=0))
        grade = attempt["grades"][f"q{index}"]
        if question.kind != "written" and grade in stats:
            stats[grade] += 1
    attempt["performance_recorded"] = True


def plan_practice(topics, profile, count, adaptive=False):
    """Allocate approximately 60/20/20; small exams use deterministic rounding.

    Weakness is a practice signal, not a mastery diagnosis. Fewer than two
    answered questions is limited evidence. Unanswered questions are separate.
    """
    if not topics:
        raise LabError("input", "Set up your learning topics before adaptive practice.")
    def stats(t):
        s = profile.get(t, {})
        return s.get("correct", 0), s.get("incorrect", 0)
    weak = sorted([t for t in topics if stats(t)[1]],
                  key=lambda t: (stats(t)[0] / sum(stats(t)), topics.index(t)))
    unseen = sorted(topics, key=lambda t: (sum(stats(t)), topics.index(t)))
    revision = sorted(topics, key=lambda t: (-sum(stats(t)), topics.index(t)))
    if not adaptive or not weak:
        return [unseen[i % len(unseen)] for i in range(count)], "Broad coverage: building evidence across your learning topics."
    weak_count = max(1, int(count * .6 + .5))
    new_count = min(count - weak_count, int(count * .2 + .5))
    groups = [(weak, weak_count), (unseen, new_count), (revision, count - weak_count - new_count)]
    plan = [pool[i % len(pool)] for pool, n in groups for i in range(n)]
    return plan, (f"{weak_count} questions target topics with incorrect answers; "
                  f"{new_count} explore less-assessed topics; {count - weak_count - new_count} revise prior topics. "
                  "Categories may overlap. One error is a practice signal, not a diagnosis.")
