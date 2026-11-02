# Changelog

## 2026-11-02 — Prepare the vector index with study material

- Moved embedding configuration and consent into Study material preparation.
- Prepare builds the Chroma index; subsequent exams reuse it without reembedding documents.
- Clear session deletes the active collection, including saved indexes, while leaving other collections untouched.
- Excluded local temporary study documents from version control.

## 2026-11-02 — Environment defaults in the interface

- Added project-root .env and process-environment defaults for generation,
  retrieval and embedding settings and provider keys, with session UI overrides.
- Default keys stay hidden; consent remains required. Clear session reapplies
  settings while retaining access to file/environment keys. No .env writes.
- Declared the already-pinned python-dotenv package as a direct dependency;
  tests isolate real configuration and verify precedence and secret handling.

## 2026-11-02 — Actionable PDF extraction errors

- PDF workers now return safe reason codes for encryption, page/text limits,
  empty extraction and parser failures. The UI reports a specific recovery action.
- Enabled tolerant pypdf parsing for recoverable formatting issues; retained
  subprocess isolation, timeout and all content limits. Raw exceptions stay hidden.

## 2026-11-02 — Larger uploads

- Raised per-file and combined collection upload limits to 10 MiB, including
  Streamlit and the isolated PDF worker. Page/text limits remain unchanged.

## 2026-11-01 — Reusable study sessions and bounded paper history

- Added explicit one-time preparation of sample, pasted or multiple uploaded
  documents; generation reuses prepared chunks and compatible vector indexes.
- Retain the latest five papers with original settings, drafts, submissions and
  results. Switching papers restores answers; successful overflow evicts oldest.
- Added collection size limits and duplicate-document detection. Failed generation
  preserves history. Clear session resets the workspace; saved indexes remain.

## 2026-11-01 — LangChain recursive chunking

- Replaced custom slicing with `RecursiveCharacterTextSplitter`, preserving
  paragraph/line boundaries and PDF page citations. Defaults remain 1,200
  characters with 200-character target overlap.
- Added stable document/chunk identities, ordering, content hashes and chunking
  metadata shared by lexical and semantic retrieval. Old saved indexes must be rebuilt.
- Added pinned `langchain-text-splitters` 1.1.3. BM25/hybrid retrieval remain pending.

## 2026-11-01 — LLM-only question generation

- Removed Demo from providers, UI, graph branches and exports; deleted the
  rule-based question generator. Every generation run now requires LLM credentials.
- Replaced tests' dependency on Demo with isolated synthetic model responses.
- Updated setup and learning instructions. Earlier entries describe past versions.

## 2026-10-31 — Interactive exams and temporary attempts

- Added single-answer, multiple-answer, written and mixed generation formats.
- Added radio/checkbox/text responses, explicit submission, local exact-set choice
  marking and written-answer manual review; answer keys appear after submission.
- Added session-only attempts, response JSON backups, mixed printable exports and
  an offline Demo covering every type. No additional dependencies or live AI calls.
- Added a beginner walkthrough explaining contracts, state, storage and testing.

## 2026-10-31 — Embedded Chroma vector database

- Replaced the semantic in-memory vector store with Chroma cosine collections.
- Temporary collections remain the default; optional local persistence includes
  saved-index reuse and explicit deletion. Source/page metadata is preserved.
- Added Chroma 1.5.9 and pinned its dependencies; ignored local database files.
- No live API calls, historical-result changes or publication.

## 2026-10-29 — Optional API semantic retrieval

- Added independent OpenAI/Gemini embedding selection, explicit consent and keys.
- Added a session-owned LangChain in-memory vector index with bounded API batches,
  cosine retrieval, configuration-aware reuse, and original source metadata.
- Both LangGraph workflows can use semantic search; blank queries retain document
  coverage. Lexical remains the default; Demo remains offline.
- No dependency additions, live API calls, historical-result changes or publishing.

## Public v0.1 — local implementation, release review pending

- Replaced FastAPI/HTML with Streamlit and interface-independent core functions.
- Added LangChain integrations, session credentials, TXT/topic inputs, difficulty,
  and separate escaped printable exam/answer-key HTML exports.
- Implemented deterministic and experimental LangGraph workflows with bounded
  execution, local validation and no private graph persistence.
- Preserved bounded PDF extraction, lexical retrieval and stable citations.
- Removed legacy endpoints, student attempt service, custom provider transports,
  Jev controller, old benchmark runtime, Docker requirements and obsolete tests.
- Preserved historical results unchanged; replaced current documentation/tests.

Public v0.1 starts a new release line. Earlier v0.4/v0.4.1 labels describe historical
experiments, not this implementation. See docs/CHANGE_REPORT.md.
