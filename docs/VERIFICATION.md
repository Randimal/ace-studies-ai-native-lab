# Public v0.1 verification — 2026-10-26

## Environment defaults follow-up — 2026-11-02

- Full offline suite: **121 passed in 57.02 seconds**, with the existing Chroma
  configuration warning. Startup and limited release checks passed; all 22
  historical hashes match.
- Config tests verify file/environment precedence, empty environment overrides,
  literal values without interpolation, safe warnings and no environment mutation.
- AppTest verifies setting defaults, hidden key fields, explicit consent, API-key
  overrides, provider switching and Clear session restoration. Tests isolate the
  user's actual .env and inherited configuration; no live AI calls were made.
- Default secrets are local server configuration, not erased by Clear session.
  Earlier snapshots describing .env as unused no longer apply to this version.

## PDF error reporting follow-up — 2026-11-02

- Focused document, PDF-error and collection suite: **40 passed in 7.02 seconds**.
- Real subprocess tests cover synthetic encrypted, over-page-limit and blank PDFs.
  Mocked tests cover extraction limits, tolerant-parser configuration, fixed safe
  messages, invalid worker payloads and process failures. Valid PDF extraction
  and timeout regression tests also pass.
- The user's failing PDF was not supplied or inspected; its exact failure remains
  unconfirmed. New diagnostics expose the category on the next upload without
  revealing raw exception details. No live AI calls or dependency changes.

## Reusable study-session follow-up — 2026-11-01

- Full suite: **102 passed in 52.60 seconds**. Existing Chroma configuration
  deprecation warning remains; no live AI API requests were made.
- AppTest verifies explicit preparation, no repeated parsing on generation,
  draft and submitted-answer restoration, five-paper eviction, failure preserving
  history, session isolation and Clear session cleanup. Existing semantic tests
  verify document embeddings are reused across successive paper generations.
- Collection tests cover multiple TXT uploads, duplicate-content IDs, combined
  size/count limits and topic-only preparation. Existing PDF extraction tests pass.
- Localhost startup and limited release checks passed; all 22 historical hashes
  match. No dependencies changed. Live/manual provider quality review is pending.
- Memory limits bound retained content, not total interpreter/library memory.
  Papers and responses are temporary, even when source vectors are saved on disk.

## LangChain chunking follow-up — 2026-11-01

- Full suite: **97 passed in 46.40 seconds**; the existing upstream Chroma
  configuration deprecation warning remains.
- Added tests for paragraph/line preservation, hard chunk-size bounds, overlap
  without text loss, repeated-content IDs, configuration changes and input limits.
- Real Chroma round-trip preserves new chunk metadata; saved-index reuse rejects
  changed chunking settings. Existing lexical, semantic, graph and UI tests pass.
- Installed pinned `langchain-text-splitters` **1.1.3** in `.venv`. Dependency
  compatibility passed for all **141** installed packages; existing pins retained.
- Localhost startup and release checks passed; all **22** historical hashes match.
  No live AI calls were made. Retrieval-quality improvements have not been measured.
- Old custom-chunker saved indexes require rebuilding; new chunk metadata and
  boundaries intentionally change their identities.

## LLM-only generation follow-up — 2026-11-01

- Removed the Demo runtime path. Updated offline tests use isolated synthetic
  responses, with no test helper imported by the application.
- Full suite: **88 passed in 55.48 seconds**; the existing Chroma configuration
  deprecation warning remains. Tests cover mandatory credentials/consent, rejection
  of the removed provider, real prompt/parsing paths with mocked model responses,
  all question formats, both workflows and interactive attempts.
- Initial verification exposed missing Chroma in the remaining `.venv`. Installed
  the existing pinned requirements there; no dependency pins were changed.
  Compatibility check passed for all **140** installed packages.
- Streamlit localhost startup passed. All **22** historical hashes match and the
  limited release pattern check passed. No live AI API requests were made.
- Earlier sections record past implementations and environments, including Demo
  and `.venv-v01`; neither describes the current generation setup.

## Interactive exam follow-up — 2026-10-31

- Full suite: **86 passed in 35.16 seconds**, zero failures; the existing upstream
  Chroma configuration deprecation warning remains.
- Added checks for all four generation formats at ten questions, invalid type
  contracts, exact-set choice marking, unanswered/manual-review status, backup
  separation and printable mixed-format papers/keys.
- Streamlit AppTest answers all three question types across reruns, submits,
  checks locked answers and delayed key visibility, and resets via Generate/Clear.
  The test rejects any generation call during answering and submission.
- No dependencies added and no live AI calls made. Real provider adherence to the
  expanded question schema and educational quality still need live/manual review.
- Attempts remain session-only. JSON downloads are readable backups, without an
  import feature. Manual grading entry, authentication and durable attempt storage
  are not implemented.

## Chroma follow-up — 2026-10-31

- Full suite: **74 passed in 68.34 seconds**, zero failures. One upstream Chroma
  deprecation warning when inspecting collection configuration.
- Actual Chroma cosine ranking, source/page metadata, collection isolation,
  persistence, mismatched-ID rejection and explicit deletion are exercised.
- A separate child process writes an index, exits, and the parent reopens it,
  establishing persistence across process restart with synthetic data.
- Scripted API embeddings verify saved-index reuse skips document embedding;
  Streamlit AppTest checks persistence is opt-in and deletion clears the index.
- All **137** installed runtime/test packages pass the dependency compatibility
  check. Chroma **1.5.9** is pinned; existing dependency pins were retained.
- Streamlit loopback startup health passed. All **22** historical files match
  their recorded hashes; limited integrity/pattern checks passed.
- No live embedding/generation calls were made. Retrieval quality and live
  provider compatibility remain unmeasured. Local persistence is not encrypted,
  authenticated multi-user storage or guaranteed secure deletion.

Earlier snapshots below describe the implementation as it existed on those dates.

## Semantic retrieval follow-up — 2026-10-29

- Full suite: **62 passed in 26.79 seconds**, zero failures.
- Both actual embedding client constructors and their timeout/retry configuration
  checked without external requests. Gemini's pinned integration needs a small
  `_build_config` override to forward bounds; this is covered by a regression test.
- Fake vectors exercise real LangChain in-memory similarity ranking, source/page
  preservation, cache reuse/invalidation/isolation, malformed vectors, safe errors,
  batching, request limits, deadlines and both LangGraph workflows.
- Streamlit AppTest verifies embedding consent gates, independent provider keys,
  reuse across Generate clicks, and clearing the session index.
- Existing dependency pins suffice; no new packages installed. No live embedding
  or generation calls were made. Semantic relevance/quality gains are unmeasured.
- Historical artifacts remain unchanged; release integrity/pattern check passed.

The sections below describe the original Task 02 verification snapshot.

## Executed locally

- Fresh environment: `.venv-v01`, Python **3.11.9**, Windows. The existing broken
  `.venv` was preserved. Installed 89 pinned runtime/test packages using uv.
- Final `python -m pytest -q --tb=short`: **48 passed in 18.79 seconds**, zero failures.
- `uv --system-certs pip check --python .venv-v01/Scripts/python.exe`: all 89
  installed packages compatible. The uv-created environment has no pip bootstrap;
  normal `python -m venv` installation instructions include pip.
- `python tools/verify_startup.py`: temporary localhost Streamlit server returned
  HTTP 200 / `ok`; process stopped in the script's finally block.
- `python tools/check_release.py`: all **22** historical evaluation hashes match;
  limited known-secret-pattern checks passed for candidate text files. File count
  depends on documentation additions; run the tool for the exact current count.

## What the tests establish

- Real bounded PDF subprocess extraction using a synthetic text PDF; TXT/paste
  loading, stable chunk IDs, page metadata, size checks and parser timeout handling.
- Lexical matching and spread-out retrieval; absent-topic insufficient evidence.
- Four-option MCQs, requested count, answer bounds, explanations, duplicate and
  citation validation; escaped answer-free examination HTML and separate key.
- Real deterministic LangGraph demo completion and scripted generation/retry paths.
- Scripted agent routing, premature-finish rejection, revision, bounded decisions,
  generation retries and rejection of late results.
- Construction of all four actual LangChain provider clients with synthetic keys;
  per-invocation key separation, safe exception messages, complete JSON parsing,
  call/token ceilings and inherited tracing suppression.
- Streamlit AppTest sample/paste generation, mocked topic-only provider generation,
  session/key isolation, clear-session behavior, download controls and no automatic
  regeneration on rerun.

Tests block external socket connections. Loopback is allowed for Windows asyncio's
internal socket pair. Mocked responses are not live provider verification.

## Limitations and release gates

- **No live AI API requests were made.** OpenAI, Gemini, Groq and Anthropic model
  compatibility and real account access remain unverified for this implementation.
- Agentic mode stays experimental; a successful live end-to-end test is pending.
- Human factual correctness, ambiguity, difficulty and pedagogical evaluation are
  pending. Structural passes and source IDs do not establish those properties.
- Python 3.11 Windows installation was verified. macOS/Linux instructions and
  configured GitHub Actions matrix have not been executed in this task.
- AppTest and HTTP health are not a full manual browser/physical print audit.
- Dependency license/notice and source ownership review remain open; see
  PROVENANCE.md. The MIT license was preserved, not independently cleared.
- The limited pattern scanner is not a comprehensive secrets/privacy audit.
  `.env`, archives and development caches stay outside publication candidates.
- No Git repository was initialized; no commit, push, deployment or publication
  occurred. Default binding is localhost; public hosting requires separate review.

The initial test iterations exposed oversized pytest parameter IDs on Windows and
a network guard that also blocked asyncio's loopback socket pair. Both test-harness
issues were corrected before the passing full-suite run above.
# 2026-11-02 — Material preparation and vector cleanup

- Offline suite: 124 passed; one Chroma legacy configuration deprecation warning.
- Streamlit localhost startup health check passed.
- Release pattern scan passed; all 22 historical files retain their recorded hashes.
- Tests verify preparation embeds documents once, later queries reuse the index,
  and both explicit index deletion and Clear session remove the active saved
  collection without deleting unrelated collections.
- No live generation or embedding API calls were made.

