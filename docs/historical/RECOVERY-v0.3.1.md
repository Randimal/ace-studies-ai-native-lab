# v0.3.1 recovery and verification — 2026-10-12

Recovery continued from the existing workspace. No implementation was restarted, no
existing files were reverted, and no commit or push was made. This workspace has
no `.git` directory: original created/modified status and the interrupted session's
exact diff cannot be reconstructed. A source-only pre-edit snapshot is retained in
`tmp/recovery_baseline.zip`; `.env` and virtual environments were excluded.

## Already present before recovery

- Optional TypeSafe Choice adapter, model discovery, safe errors, response limits,
  confidence policy, and explicit smoke CLI in `app/decision_controllers/`.
- Controller selection in document options and the existing single LangGraph
  decide/retrieve/generate/validate/finish loop; finite choices mapped to allowed
  server-owned actions, shared execution limits, and final quiz validation.
- Separate controller/generation calls, latency, reported usage, completeness,
  cost estimates, uncertainty events, and content-free traces.
- Three workflow UI choices and three-way benchmark/report support.
- Mocked Jev and hybrid benchmark tests, environment isolation, README,
  architecture documentation, and a synthetic Docker verification script.

All 40 application/test Python files parsed before changes. The recovered focused
Jev, hybrid benchmark, agent, and comparison suite passed 93 tests.

## Gaps completed

1. Removed the unintended Groq-only restriction in the graph, UI, and benchmark
   help. Jev now controls decisions while any existing configured cloud/local
   generation adapter writes quizzes. Offline demo remains deterministic.
2. Checked the current official Swagger/OpenAPI contract at
   <https://api.typesafe.ai/docs> and <https://api.typesafe.ai/openapi.json>
   (API version 0.2.0). Existing request fields and response fields matched;
   restored its required nonempty `answers` constraint in the response model.
   No undocumented request or response fields were introduced.
3. Added a deadline check after graph nodes, including final local validation,
   so a late validated result cannot be published. Deadlines remain cooperative;
   blocking operations are not forcibly cancelled.
4. Added mocked hybrid generation and three-way benchmark coverage for all six
   existing live/local provider adapters, malformed documented envelopes,
   oversized responses, optional configuration independence, and late final
   validation rejection.
5. Updated setup, UI notices, architecture, roadmap, and optional configuration
   comments to describe the selected generation provider accurately.

Retrieval, generation prompts, provider wire adapters, quiz validators, student
attempts, legacy endpoints, and infrastructure requirements were reused.
No database, cooperating agents, or commercial Ace Studies changes were added.

## Changed files

- `app/agent.py`
- `app/benchmark.py`
- `app/decision_controllers/jev.py`
- `app/index.html`
- `tests/test_jev.py`
- `tests/test_hybrid_benchmark.py`
- `.env.example`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- This recovery report.

Verification artifacts: `tmp/Dockerfile.verify`, `tmp/recovery_baseline.zip`, and
`tmp/recovery.patch`. The pre-existing `tmp/verify_v031.py` was reused unchanged.
The verification image adds pytest separately; production dependencies and the
production Dockerfile/Compose configuration were unchanged.

## Verification results

- Final complete suite in the Python 3.12 verification image: **405 passed in
  46.49 seconds**. Provider HTTP transport was mocked; local credentials were
  cleared by test fixtures. This includes deterministic, LLM-agentic, Jev hybrid,
  all generation adapters, endpoints, Student Mode, benchmarks, and legacy APIs.
- The first container run exposed the missing nonempty-answer constraint through
  a new regression test (399 passed, one failed); it was fixed before the final
  passing run. No final test failures remain.
- Python compilation: **40 application/test files passed**.
- UI JavaScript parsed successfully with Node.
- `docker compose build` and `docker compose up -d` succeeded for the final code.
- Running Compose HTTP checks passed: health reports v0.3.1, UI serves all three
  workflow choices, no-key Student Mode withholds answers, and the legacy demo
  endpoint retains its original architecture/contract.
- `tmp/verify_v031.py` passed in Docker: real LangGraph execution with mocked
  TypeSafe/Groq responses, three-way benchmark, student confidentiality, and
  submission. All three benchmark runs completed without generation failures.
- Optional Jev smoke command in an isolated container printed **SKIP** because
  that invocation received no TypeSafe key. No live TypeSafe or generation-provider
  request was made during recovery. Live compatibility/access remains unverified.
- `git diff --check` cannot run without repository metadata. The recorded recovery
  diff was checked for trailing whitespace on added lines: **zero issues**.

The duplicate Windows full-suite run was stopped after the final container suite
passed; the earlier focused Windows suite had completed successfully.

## Remaining verification

An operator with TypeSafe access can explicitly run the documented synthetic
Choice smoke test or model discovery command. A successful one-call smoke test
still does not validate the entire live hybrid workflow or establish quality,
latency, or cost advantages. Live multi-provider comparisons remain a separate
experiment. Unknown costs and factual grounding remain unknown/not evaluated.

The Compose service is left running at <http://localhost:8000>.
