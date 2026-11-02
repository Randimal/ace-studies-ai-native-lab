"""Embedded Chroma collections. No server, default embeddings, or API secrets."""
import json
from pathlib import Path
import re
import uuid
import weakref

from langchain_core.documents import Document

from .validation import LabError

DATABASE_PATH = Path(__file__).resolve().parents[1] / ".local" / "chroma"


def _delete_quietly(client, name):
    try:
        client.delete_collection(name)
    except Exception:
        pass  # Best-effort GC cleanup; explicit delete reports failures.


class ChromaIndex:
    def __init__(self, *, persistent=False, path=None):
        import chromadb
        from chromadb.config import Settings
        self.persistent = persistent
        self.collection = None
        self._finalizer = None
        try:
            settings = Settings(anonymized_telemetry=False)
            self.client = (chromadb.PersistentClient(path=str(path or DATABASE_PATH), settings=settings)
                           if persistent else chromadb.EphemeralClient(settings=settings))
        except Exception:
            raise LabError("vector_db", "The local vector database could not be opened.") from None

    @property
    def name(self):
        return self.collection.name if self.collection is not None else ""

    @property
    def dimension(self):
        return self.collection.metadata["dimension"]

    def restore(self, name, identity):
        if not self.persistent or not re.fullmatch(r"ace-[0-9a-f]{32}", name):
            raise LabError("vector_db", "Enter a valid saved index ID, or leave it blank to create a new index.")
        try:
            collection = self.client.get_collection(name=name, embedding_function=None)
            if collection.metadata.get("identity") != identity or collection.count() == 0:
                raise ValueError()
        except Exception:
            raise LabError("vector_db", "Saved index is unavailable or does not match this document and embedding configuration. Leave the saved ID blank to build a new index.") from None
        self.collection = collection

    def build(self, documents, vectors, identity):
        name = "ace-" + uuid.uuid4().hex
        try:
            # We supply vectors explicitly. Chroma must never download a model
            # or store a provider embedding function (which could contain keys).
            self.collection = self.client.create_collection(
                name=name, embedding_function=None,
                configuration={"hnsw": {"space": "cosine"}},
                metadata={"identity": identity, "dimension": len(vectors[0])},
            )
            self.collection.add(
                ids=[d.metadata["source_id"] for d in documents], embeddings=vectors,
                documents=[d.page_content for d in documents],
                metadatas=[{"source_metadata": json.dumps(d.metadata, sort_keys=True)} for d in documents],
            )
            if not self.persistent:
                self._finalizer = weakref.finalize(self, _delete_quietly, self.client, name)
        except Exception:
            if self.collection is not None:
                _delete_quietly(self.client, name)
            self.collection = None
            raise LabError("vector_db", "The vector index could not be built. No partial index will be reused.") from None

    def search(self, vector, count):
        try:
            result = self.collection.query(query_embeddings=[vector], n_results=count,
                                           include=["documents", "metadatas"])
            return [Document(page_content=text, metadata=json.loads(metadata["source_metadata"]))
                    for text, metadata in zip(result["documents"][0], result["metadatas"][0], strict=True)]
        except Exception:
            raise LabError("vector_db", "The vector database query failed. Rebuild the index and try again.") from None

    def delete(self):
        if self.collection is None:
            return
        try:
            self.client.delete_collection(self.name)
            if self._finalizer:
                self._finalizer.detach()
            self.collection = None
        except Exception:
            raise LabError("vector_db", "The index could not be deleted. It may still exist locally.") from None


def clear_index(cache, *, delete_saved=False):
    """Release this session's index; persistent data survives unless requested."""
    store = cache.get("store")
    if isinstance(store, ChromaIndex) and (delete_saved or not store.persistent):
        store.delete()
    cache.clear()
