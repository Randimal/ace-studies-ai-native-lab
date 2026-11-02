# Task 02 source-file change report

## Environment-default follow-up on 2026-11-02

Added `core/config.py` and `tests/test_config.py`; updated `app.py`, test isolation
and UI tests, environment template, dependency declarations and current docs.
The project-root .env is now read at runtime, without printing or modifying it.
Earlier reports describing .env as unused refer to earlier versions.

## Study-session follow-up on 2026-11-01

Added `core/study_session.py` and `tests/test_study_session.py`. Updated `app.py`,
UI tests, README, learning guide, changelog, verification and this report for
one-time material preparation, multiple uploads and five-paper session history.
No dependency changes; historical benchmark artifacts remain untouched.

## LangChain chunking follow-up on 2026-11-01

Updated `core/documents.py` to use LangChain recursive text splitting and retain
structural whitespace and versioned chunk metadata. Updated document and semantic
tests, dependency manifests, README, learning guide, changelog, verification and
this report. No changes to lexical scoring, embedding providers or graph routing.
Historical evaluation files are unchanged; saved old-format indexes need rebuilding.

## LLM-only follow-up on 2026-11-01

Removed Demo behavior from `app.py`, `core/providers.py`, `core/graph.py`,
`core/generation.py` and `core/export.py`. Added test-only response fixtures in
`tests/helpers.py` and a test package marker; updated workflow, provider, semantic,
attempt and UI tests. Updated README, learning guide, changelog, verification and
the environment template. Historical artifacts retain their original contents.

## Interactive exam follow-up on 2026-10-31

Added `core/attempts.py`, `tests/test_attempts.py` and `docs/LEARNING_GUIDE.md`.
Updated `app.py`, `core/validation.py`, `core/generation.py`, `core/export.py`,
Streamlit tests, README, changelog, verification and this report. Attempt storage
is session-only; Chroma remains dedicated to source retrieval. Historical files
and dependency pins are unchanged.

## Follow-up on 2026-10-31

Added `core/vector_db.py` and `tests/test_vector_db.py`. Modified `core/semantic.py`,
`app.py`, semantic/Streamlit tests, `.gitignore`, `requirements.in`,
`requirements.txt`, README, changelog, provenance, verification and this report.
Chroma replaces the previous semantic vector store, with temporary collections by
default and explicit local persistence, saved-ID reuse and deletion controls.
Existing dependency pins were retained while adding Chroma and its dependencies.

## Follow-up on 2026-10-29

Added `core/semantic.py` and `tests/test_semantic.py`. Modified `app.py`,
`core/graph.py`, `tests/test_streamlit.py`, `README.md`, `CHANGELOG.md`,
`docs/VERIFICATION.md`, and this report for optional API semantic retrieval.
No source files were removed and no dependency versions changed in this follow-up.
The lists below preserve the original Task 02 change inventory.

Paths are relative to the project root. Historical evaluation artifacts remain unchanged.

## Created

- `.streamlit/config.toml`
- `CHANGELOG.md`
- `app.py`
- `core/__init__.py`
- `core/documents.py`
- `core/export.py`
- `core/generation.py`
- `core/graph.py`
- `core/pdf_worker.py`
- `core/providers.py`
- `core/retrieval.py`
- `core/validation.py`
- `docs/CHANGE_REPORT.md`
- `docs/PROVENANCE.md`
- `docs/VERIFICATION.md`
- `docs/historical/README.md`
- `docs/historical/sha256.json`
- `examples/study_notes.txt`
- `requirements.in`
- `tests/test_documents.py`
- `tests/test_streamlit.py`
- `tests/test_validation_exports.py`
- `tests/test_workflows.py`
- `tools/check_release.py`
- `tools/verify_startup.py`

## Modified

- `.env.example`
- `.github/workflows/tests.yml`
- `.gitignore`
- `README.md`
- `requirements-dev.txt`
- `requirements.txt`
- `tests/conftest.py`
- `tests/test_providers.py`

## Moved

- `docs/ARCHITECTURE.md → docs/historical/ARCHITECTURE.md (bytes unchanged)`
- `docs/BENCHMARK-DIAGNOSIS-v0.4.md → docs/historical/BENCHMARK-DIAGNOSIS-v0.4.md (bytes unchanged)`
- `docs/BENCHMARK.md → docs/historical/BENCHMARK.md (bytes unchanged)`
- `docs/RECOVERY-v0.3.1.md → docs/historical/RECOVERY-v0.3.1.md (bytes unchanged)`
- `docs/ROADMAP.md → docs/historical/ROADMAP.md (bytes unchanged)`

## Removed or replaced

- `.dockerignore`
- `Dockerfile`
- `app/__init__.py`
- `app/agent.py`
- `app/attempts.py`
- `app/benchmark.py`
- `app/benchmark_experiment.py`
- `app/decision_controllers/__init__.py`
- `app/decision_controllers/jev.py`
- `app/decision_controllers/smoke.py`
- `app/document_flow.py`
- `app/document_schemas.py`
- `app/documents.py`
- `app/evaluation.py`
- `app/execution.py`
- `app/generation.py`
- `app/grounding.py`
- `app/index.html`
- `app/llm.py`
- `app/main.py`
- `app/pdf_worker.py`
- `app/pipeline.py`
- `app/provider_diagnostics.py`
- `app/providers/__init__.py`
- `app/providers/adapters.py`
- `app/providers/config.py`
- `app/quality.py`
- `app/retrieval.py`
- `app/schemas.py`
- `app/smoke.py`
- `compose.yaml`
- `tests/Dockerfile`
- `tests/test_agent.py`
- `tests/test_app.py`
- `tests/test_attempts.py`
- `tests/test_benchmark.py`
- `tests/test_benchmark_experiment.py`
- `tests/test_cleanup.py`
- `tests/test_comparison.py`
- `tests/test_document_flow.py`
- `tests/test_document_processing.py`
- `tests/test_evaluation.py`
- `tests/test_hybrid_benchmark.py`
- `tests/test_jev.py`
- `tests/test_provider_diagnostics.py`
- `tests/test_quality.py`
- `tests/test_retrieval.py`

## Significant removals

The old FastAPI runtime, HTML/JavaScript UI, student-attempt service, legacy exam
contracts, custom HTTP adapters, Jev controller and benchmark execution modules
were removed from the active source. Tests that depended on those contracts were
replaced with tests of the new application. Dockerfiles and Compose were removed.
No compatibility shim or second application was created.

## Preserved local material

- `.env` and other existing user-owned secret files were not deleted or loaded.
- `tmp/pre-public-v01-source.zip` contains the pre-refactor source/config/docs
  backup (60 files), excludes `.env`, and is ignored. It is not a public artifact.
- `tmp/refactor_backup.py`, `tmp/write_v01_docs.py`, `tmp/report_changes.py`, and
  `tmp/removed-v01.json` are ignored one-off migration helpers, not runtime files.
- `.venv-v01` is the fresh Python 3.11.9 environment; the previous `.venv` remains.
- Existing recovery material, OS cache directory and Python caches are ignored,
  not included in candidate publication contents.
- All 22 original `evaluation/` files remain at their original paths and hashes.

An ownership-cleared historical source snapshot is still needed if the old
experiments are to be independently rerunnable from the public repository.
# 2026-11-02 — Material preparation and vector cleanup

Embedding provider, model, key and consent now belong to Study material.
Prepare builds the Chroma collection before marking material ready. Exam
generation reuses the prepared index; it cannot silently rebuild a missing one.
Clear session deletes its active collection, including persistent collections.
Other collections remain intact. Local temporary study documents are Git-ignored.

