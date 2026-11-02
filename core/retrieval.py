"""Small lexical RAG: relevance for a topic, spread-out coverage otherwise."""
import re
from langchain_core.documents import Document
from .validation import LabError


def retrieve(documents: list[Document], query: str = "", limit: int = 8, byte_budget: int = 16_000) -> list[Document]:
    terms = set(re.findall(r"\w+", query.casefold())) - {"the", "a", "an", "of", "and", "to", "in"}
    if terms:
        scored = [(sum(term in set(re.findall(r"\w+", doc.page_content.casefold())) for term in terms), i)
                  for i, doc in enumerate(documents)]
        indices = [i for score, i in sorted(scored, key=lambda item: (-item[0], item[1])) if score]
    else:
        count = min(limit, len(documents))
        indices = ([len(documents) // 2] if count == 1 else
                   [round(i * (len(documents) - 1) / (count - 1)) for i in range(count)])
    selected, used = [], 0
    for i in indices:
        doc = documents[i]
        size = len(doc.page_content.encode("utf-8")) + 100
        if used + size <= byte_budget:
            selected.append(doc)
            used += size
        if len(selected) == limit:
            break
    if not selected:
        raise LabError("insufficient_evidence", "No source passages match or fit. Broaden the topic, shorten the source, or add relevant notes.")
    return selected
