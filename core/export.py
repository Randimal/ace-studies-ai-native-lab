"""Standalone escaped HTML. The exam projection never contains teacher fields."""
from html import escape
from .validation import Exam


def export_html(exam: Exam, *, answer_key: bool = False, basis: str = "document") -> str:
    title = "Answer key" if answer_key else "Examination paper"
    rows = []
    for number, q in enumerate(exam.questions, 1):
        body = f"<h2>{number}. {escape(q.question)}</h2>"
        if answer_key:
            indices = [q.answer_index] if q.kind == "single" else q.answer_indices
            for index in indices:
                body += f"<p><strong>{chr(65 + index)}. {escape(q.options[index])}</strong></p>"
            if q.kind == "written":
                body += f"<p>Manual review rubric: {escape(q.rubric)}</p>"
            body += f"<p>{escape(q.explanation)}</p>"
            if q.source_ids:
                body += "<p class='muted'>References: " + escape(", ".join(q.source_ids)) + "</p>"
        else:
            instruction = {"single": "Select one answer.", "multiple": "Select all correct answers.", "written": "Write a short answer."}[q.kind]
            body += f"<p>{instruction}</p>"
            if q.kind == "written":
                body += "<p>________________________________________________________________</p>" * 3
            else:
                body += "<ol type='A'>" + "".join(f"<li>{escape(option)}</li>" for option in q.options) + "</ol>"
        rows.append("<section>" + body + "</section>")
    notice = "Document-based; references do not verify factual correctness." if basis == "document" else "Generated from model knowledge; no supplied document evidence."
    return "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>" + title + "</title><style>body{font:16px Georgia,serif;max-width:800px;margin:40px auto;padding:0 24px;color:#17212b}h1{font-size:28px}h2{font-size:18px}section{break-inside:avoid;margin:28px 0}li{margin:8px 0}.muted{color:#555;font-size:13px}@media print{body{margin:0;max-width:none}@page{margin:18mm}}</style></head><body><h1>" + title + "</h1><p>Ace Studies AI-Native Lab</p><p class='muted'>" + notice + "</p>" + ("" if answer_key else "<p>Name: ____________________ &nbsp; Date: __________</p><p>Follow the answer instructions for each question.</p>") + "".join(rows) + "</body></html>"
