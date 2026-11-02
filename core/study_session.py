"""Bounded study material and exam history; independent of Streamlit."""
from .attempts import new_attempt
from .documents import load_text, load_upload, MAX_UPLOAD_BYTES, MAX_CHARS, MAX_PAGES
from .validation import LabError

MAX_PAPERS = 5
MAX_FILES = 10


def prepare_material(mode, *, text="", uploads=()):
    """Prepare once. Store chunks, not copies of raw uploaded files."""
    if mode == "Topic only":
        return {"mode": mode, "documents": [], "names": []}
    if mode != "Upload PDF / TXT":
        return {"mode": mode, "documents": load_text(text), "names": [mode]}
    if not uploads or len(uploads) > MAX_FILES:
        raise LabError("input", f"Choose between 1 and {MAX_FILES} PDF or TXT files.")
    if sum(len(data) for _, data in uploads) > MAX_UPLOAD_BYTES:
        raise LabError("input", "Combined uploads must be at most 10 MiB.")
    documents, names, seen, page_count, characters = [], [], set(), 0, 0
    for name, data in uploads:
        chunks = load_upload(data, name)
        document_id = chunks[0].metadata["document_id"]
        if document_id in seen:
            continue  # Identical documents must not create duplicate Chroma IDs.
        seen.add(document_id)
        page_count += len({d.metadata["page"] for d in chunks if d.metadata["page"] is not None})
        characters += sum(len(d.page_content) for d in chunks)
        if page_count > MAX_PAGES or characters > MAX_CHARS:
            raise LabError("input", "Combined material exceeds 50 nonempty PDF pages or 100,000 chunk characters (including overlap).")
        for chunk in chunks:
            chunk.metadata["source_name"] = name
        documents.extend(chunks)
        names.append(name)
    return {"mode": mode, "documents": documents, "names": names}


def add_paper(history, result, request, provider, model, number):
    """Keep the newest five successful papers. Failed runs never call this."""
    paper = {"result": result, "attempt": new_attempt(result["exam"]),
             "request": request.model_dump(), "provider": provider, "model": model,
             "number": number}
    history.append(paper)
    removed = history.pop(0) if len(history) > MAX_PAPERS else None
    return paper, removed
