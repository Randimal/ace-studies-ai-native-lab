"""Bounded API embeddings + session-owned embedded Chroma retrieval."""
from dataclasses import dataclass, field
import hashlib
import json
import math
import time

from langsmith import tracing_context
from pydantic import SecretStr

from .providers import ProviderSettings
from .retrieval import retrieve
from .validation import LabError
from .vector_db import ChromaIndex, clear_index

EMBEDDING_MODELS = {"OpenAI": "text-embedding-3-small", "Google Gemini": "gemini-embedding-001"}


@dataclass(frozen=True)
class EmbeddingSettings:
    provider: str
    model: str
    api_key: SecretStr = field(repr=False)

    def __post_init__(self):
        if self.provider not in EMBEDDING_MODELS:
            raise LabError("configuration", "Choose OpenAI or Google Gemini for embeddings.")
        ProviderSettings(self.provider, self.model, self.api_key)


def create_embeddings(settings, timeout):
    key = settings.api_key.get_secret_value()
    if settings.provider == "OpenAI":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=settings.model, api_key=key,
                                base_url="https://api.openai.com/v1", request_timeout=timeout,
                                max_retries=0, chunk_size=8, check_embedding_ctx_length=False)
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from google.genai.types import HttpOptions, HttpRetryOptions

    class BoundedGoogleEmbeddings(GoogleGenerativeAIEmbeddings):
        # The pinned integration accepts request_options but does not forward
        # them to embed_content. Attach bounds to its actual per-call config.
        def _build_config(self, **kwargs):
            config = super()._build_config(**kwargs)
            config.http_options = HttpOptions(timeout=max(1, int(timeout * 1000)),
                                              retry_options=HttpRetryOptions(attempts=1))
            return config

    return BoundedGoogleEmbeddings(model=settings.model, api_key=key, vertexai=False,
                                   base_url="https://generativelanguage.googleapis.com/")


class SemanticRetriever:
    """One run's embedding budget; cache contains vectors/text, never API keys.

    The caller owns the cache (Streamlit session_state, never st.cache_resource).
    Empty queries deliberately use document coverage without embedding calls.
    """
    def __init__(self, settings: EmbeddingSettings, cache: dict | None = None, *,
                 persistent=False, resume_id="", database_path=None, prepared_only=False):
        self.settings = settings
        self.cache = cache if cache is not None else {}
        self.calls = self.input_bytes = 0
        self.cache_hit = False
        self.deadline = time.monotonic() + 120
        self.persistent = persistent
        self.resume_id = resume_id.strip()
        self.database_path = database_path
        self.prepared_only = prepared_only

    def _embed(self, texts, *, query=False):
        remaining = self.deadline - time.monotonic()
        size = sum(len(text.encode("utf-8")) for text in texts)
        if remaining <= 0:
            raise LabError("timeout", "Embedding execution time limit reached.")
        if self.calls >= 32 or self.input_bytes + size > 600_000:
            raise LabError("embedding_limit", "Embedding request/input limit reached. Shorten the document.")
        self.calls += 1
        self.input_bytes += size
        try:
            with tracing_context(enabled=False, parent=False):
                model = create_embeddings(self.settings, min(30, remaining))
                vectors = [model.embed_query(texts[0])] if query else model.embed_documents(texts)
            if len(vectors) != len(texts) or not vectors:
                raise ValueError()
            dimension = len(vectors[0])
            if not 1 <= dimension <= 8192 or any(len(v) != dimension or
                    not all(math.isfinite(x) for x in v) or not any(x != 0 for x in v) for v in vectors):
                raise ValueError()
        except Exception:
            raise LabError("embedding", "Embedding request failed or returned invalid vectors. Check the embedding key, model, quota, and connection.") from None
        if time.monotonic() >= self.deadline:
            raise LabError("timeout", "Embedding execution time limit reached.")
        return vectors

    def _identity(self, documents):
        # Document/configuration identity may be persisted. Credential digest is
        # held ONLY in session memory and is never passed to Chroma.
        return hashlib.sha256(json.dumps([
            self.settings.provider, self.settings.model,
            [(doc.page_content, doc.metadata) for doc in documents],
        ], sort_keys=True).encode()).hexdigest()

    def prepare(self, documents):
        """Embed/store documents without creating a query embedding or an exam."""
        identity = self._identity(documents)
        credential = hashlib.sha256(self.settings.api_key.get_secret_value().encode()).hexdigest()
        if (self.cache.get("identity") != identity or self.cache.get("credential") != credential
                or self.cache.get("persistent") != self.persistent
                or self.cache.get("resume_id", "") != self.resume_id):
            clear_index(self.cache)
            store = ChromaIndex(persistent=self.persistent, path=self.database_path)
            if self.resume_id:
                store.restore(self.resume_id, identity)
                self.cache.update(identity=identity, credential=credential, store=store,
                                  dimension=store.dimension, persistent=self.persistent, resume_id=self.resume_id)
                self.cache_hit = True
        if self.cache.get("identity") != identity:
            vectors, batch = [], []
            for doc in documents:
                if len(doc.page_content.encode()) > 12_000:
                    raise LabError("input", "Source chunks exceed the embedding input limit.")
                if batch and (len(batch) >= 8 or sum(len(t.encode()) for t in batch) + len(doc.page_content.encode()) > 12_000):
                    vectors.extend(self._embed(batch))
                    batch = []
                batch.append(doc.page_content)
            if batch:
                vectors.extend(self._embed(batch))
            if not vectors or any(len(vector) != len(vectors[0]) for vector in vectors):
                raise LabError("embedding", "Embedding dimensions changed between batches.")
            store.build(documents, vectors, identity)
            self.cache.update(identity=identity, credential=credential, store=store, dimension=len(vectors[0]),
                              persistent=self.persistent, resume_id=self.resume_id)
        else:
            self.cache_hit = True

    def __call__(self, documents, query="", limit=8, byte_budget=16_000):
        if self.prepared_only:
            if self.cache.get("identity") != self._identity(documents) or "store" not in self.cache:
                raise LabError("vector_db", "The prepared index is unavailable. Clear session and prepare the material again.")
            self.cache_hit = True
        if not query.strip():
            return retrieve(documents, "", limit, byte_budget)
        if not self.prepared_only:
            self.prepare(documents)
        vector = self._embed([query], query=True)[0]
        if len(vector) != self.cache["dimension"]:
            raise LabError("embedding", "Query and document embedding dimensions do not match.")
        ranked = self.cache["store"].search(vector, count=len(documents))
        selected, used = [], 0
        for doc in ranked:
            size = len(doc.page_content.encode()) + 100
            if used + size <= byte_budget:
                selected.append(doc)
                used += size
            if len(selected) == limit:
                break
        if not selected:
            raise LabError("insufficient_evidence", "No passages fit the retrieval budget.")
        return selected
