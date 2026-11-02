
# v0.4.1 — Safe request diagnostics and optional pacing

`provider_diagnostics.py` wraps one adapter invocation at a time and records only finite/numeric request metadata in additive `UsageMetrics.provider_attempts`. REST adapters record actual upstream status and an allowlist of parsed Retry-After/rate-limit fields; unknown/invalid values remain unknown. Finish reasons use a finite allowlist. No raw response, request body, secret, arbitrary header, URL or provider error body enters the new diagnostic record. Existing accepted-quiz exports remain available for human review.

Compatibility API error codes/statuses remain, including `unavailable` for upstream 429/5xx. Additive cause codes and benchmark `error_category` distinguish `provider_rate_limit`, `provider_server_error`, network/timeout errors, incomplete/invalid controller output, unsupported actions/preconditions and quiz validation. The same cumulative three-unsuccessful-decisions threshold remains; provider exceptions are re-raised on termination rather than relabelled invalid model output. `decision_failures` retains its historical cumulative-guard meaning; `controller_output_failures` counts actual output rejections. Original model feedback codes, decision prompts, action preconditions, tool routing, schemas, validators and 512-token controller cap remain unchanged.

The benchmark optionally sets a context-local shared RequestPacer across all executions. Existing ExecutionBudget.before_call consults it before incrementing actual attempt counters, then rechecks/clamps the unchanged deadline. Smooth RPM spacing, rolling 60-second conservative TPM reservations and provider retry/reset cooldowns apply equally to generator/controller/retry calls. Waits are bounded and separately metered; no pacing occurs in ordinary app requests. The pacer is sequential and process-local, with recent checkpointed reservations/cooldowns restored on resume. It cannot coordinate unrelated clients or uncheckpointed in-flight requests.

Report version 3.1/app version 0.4.1 adds provider event/outcome counts and separates per-execution wall-clock, pacing wait, provider execution and inter-execution wait. Historical diagnostics stay null. The original Pilot 1 directory is protected from benchmark writes, including report/template regeneration; future conditions use new directories. See [BENCHMARK.md](BENCHMARK.md#v041-reliability-and-diagnostics) for exact CLI configuration, diagnostic codes and limits.

# v0.4 — Controlled benchmark orchestration

`app.benchmark` retains `run_baseline` and `run_comparison`, with an optional fixed question-count override. `--mode` delegates scheduling/artifacts to `benchmark_experiment.py`. Smoke schedules one pair; full schedules thirty Groq executions; custom permits selected workflows/repetitions. Runs are sequential, reversing order each pair. The runner invokes the existing baseline one case at a time, preserving provider metrics, schemas, retrieval, prompts and LangGraph decisions.

Shared CLI-only limits are restored after execution. A request-local context variable carries optional Groq sampling into immutable provider configuration and the existing wire adapter; ordinary API contracts/settings remain unchanged. Unsupported sampling requests are recorded. Offline smoke substitutes a scripted benchmark transport and does not enable offline agentic application requests.

Sanitized configuration, code/dataset identities and a schedule are checkpointed in `results.json`. Each finished execution is atomically flushed before CSV/report export. Resume validates configuration and job identities, skipping completed failures and successes. An interrupted in-flight request before checkpointing may repeat; use one writer per directory. No database or remote tracing/upload is added.

Blind UUIDs allow separate reviewer templates and analyst architecture keys. Reporting rejects invalid scores and duplicate/unknown review IDs, retaining absent factual review as unevaluated. Complete usage, unknown costs, failure denominators and small-sample P95 cautions are explicit. Read [BENCHMARK.md](BENCHMARK.md) for exact commands, limits, charges, rubric and limitations. Legacy live benchmark CLI calls also require `--allow-live`.

# v0.3.1 — Optional TypeSafe Jev controller

The integration point is the existing LangGraph decide node. DocumentOptions.decision_controller defaults to llm; jev selects app/decision_controllers/jev.py. Retrieve/generate/validate/finish nodes, state, services and validators are reused. Jev hybrid reuses any configured cloud or local quiz-generation provider; TypeSafe remains optional for the original workflows.

The adapter implements the documented Choice subset, not a general text provider. Fixed HTTPS endpoints, Authorization Bearer authentication, bounded responses/timeouts, no redirects/environment proxies and no internal retries preserve the existing security approach. Model discovery is explicit. Credentials are server-only and excluded from representations, prompts, metrics and errors.

The inspected [OpenAPI schema](https://api.typesafe.ai/openapi.json) is version 0.2.0 (2026-10-12):

- POST /v1/systemone request: model, state, questions keyed by application-defined names. Our next_action question has type choice, instructions and criteria.
- Response: model, answers.next_action with type, choice, confidence and probabilities, plus usage.input_tokens/output_tokens.
- GET /v1/models returns models with name, description and release_date. Account access determines availability.

Only currently allowed choice names are accepted. Probability keys must exactly match offered choices, values must be finite within [0,1], the sum must be within 0.02 of one, and the selected choice must have a highest probability (ties within 1e-6 allowed). Confidence is independently range-checked; it is not assumed equal to the selected probability. Invalid types/actions cannot execute tools.

Finite mappings: retrieve_topic uses the original topic; retrieve_general uses null; generate_retry requests a fresh draft; generate_revise includes the previous untrusted draft; validate invokes shared checks; finish requires a validated draft and revalidates; stop maps to cannot_complete. All current evidence is used. Jev cannot write queries or arbitrary arguments. This reduced interface is an experimental difference.

TypeSafe receives topic and workflow metadata, never passages/drafts/solutions. Controller events contain only finite choice/probability data, step, threshold/policy and no-fallback status. Existing content-free LangGraph traces retain their shape. LangSmith remains disabled; no persistence is introduced.

No confidence threshold is assumed. Record policy flags configured low confidence while continuing; fail requires an explicit threshold and stops without fallback. Invalid/transient responses share the three-unsuccessful-decision bound. Every controller call consumes shared model-call/token/deadline budgets; quiz-attempt limits count quiz generations only. The API has no documented output cap: 512 reserved output units are accounting bounds, not request fields. Reported usage is checked afterward.

CallMeter shares usage/cost aggregation for controller and generator components. Metrics distinguish calls, provider/model (including the last reported Jev revision), HTTP/parse latency, tokens, completeness and configured cost estimates. Total hybrid cost is known only when every called component has a complete estimate. Unavailable token/cost measurements stay null. Top-level provider/model identifies quiz generation; aggregate tokens cover both models.

Benchmark --workflow all runs fixed, LLM-agentic and Jev-agentic over the same cases and selected quiz provider/model. Existing both mode is preserved. Report 2.1 includes component summaries, safe TypeSafe settings and uncertainty/fallback counters. Architecture and controller-model comparisons answer different questions. Fixed order, cold imports, stochasticity and finite Jev arguments remain confounders; vendor claims are not our measurements. Structural validity/citations do not establish factual grounding.

Historical v0.3 and earlier sections below describe the preserved foundation.

# v0.3 — One model-directed LangGraph controller

The default fixed workflow retains its prompt, retries, schemas, providers, processing, retrieval and student-attempt semantics. The experimental difference is the execution controller. `DocumentOptions.workflow` defaults to `deterministic`; `document_flow.py` dispatches only explicitly selected `agentic` calls. The legacy exam API remains fixed.

## Graph and state

`app/agent.py` defines Pydantic `Decision` and typed `AgentState`. Decision fields are an allowlisted action, finite reason code, bounded optional retrieval query, existing context references, and retry/revise strategy. Extra fields, invented references, invalid strategies, incomplete/malformed outputs, and actions whose preconditions are absent are rejected before execution. Native provider tool calling is unnecessary; existing structured-output paths and local JSON validation are used.

State contains the current decision/route, latest candidate and completeness flag, deterministic validation status, validated questions, evidence IDs, and server-owned feedback codes. Document/passages and provider configuration stay in the request-scoped controller context. No credential fields enter model state. Candidate content is transient and is included in a generation call only when the model explicitly chooses revision. No conversation history is retained.

Nodes:

- `decide`: calls the selected provider/model with the decision schema, available actions, current evidence, budget status and feedback. The validated action selects a real conditional graph edge. Invalid decisions loop only within the decision/step/call limits.
- `retrieve`: calls the shared `GroundingContext.retrieve` / `LexicalRetriever` with the selected bounded query. A change of evidence clears the previous candidate and validation status. No-match feedback can cause a later model-selected query or general retrieval.
- `generate`: calls the existing adapter using the shared rendered quiz prompt and schema. It can retry or revise a prior candidate. Selected context references must be a subset of retrieved IDs. Every attempted provider generation, including failures, consumes the same generation-attempt limit as the baseline.
- `validate`: invokes the existing count/schema/option/quality/source validators. Feedback is a constant code; raw Pydantic errors, private strings and model responses never enter public traces.
- `finish`: accepts a model-selected success only after validation and repeats the final deterministic gate. An explicit cannot-complete decision ends in a safe failure. The model cannot replace server-attached citations or bypass checks.

`START -> decide`, conditional edges to allowed actions, tool edges back to `decide`, and `finish -> END` implement the loop. There is no mandatory retrieve/generate/validate schedule beyond genuine data dependencies: models can retrieve repeatedly, replace drafts, recover differently, validate again or abandon. Graph compilation uses `debug=False`, no checkpointer/cache, and no external callbacks. Invocation runs inside `langsmith.tracing_context(enabled=False, parent=False)`; no raw-state streaming is exposed. See the [LangGraph graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) and [tracing context reference](https://reference.langchain.com/python/langsmith/run_helpers/tracing_context).

## Shared services and bounds

`grounding.py` separates retrieval and prompt rendering so fixed execution still prepares evidence once while the agent invokes those operations separately. `generation.py` retains the fixed retry/controller path and now counts its calls. `execution.py` shares conservative budgets and exact provider-usage/cost aggregation. `document_flow.py` reuses the same response/evaluation assembly for either result. No provider wire protocols, endpoint allowlists, document parsers, lexical ranking, quiz quality rules or answer-key validation were replaced.

Agent defaults: 24 executed graph nodes, 12 model calls, 100,000 conservative budget units, 120 seconds; at most three unsuccessful decisions. Generation attempts are always `1 + LLM_MAX_RETRIES`, shared with fixed execution. The LangGraph recursion limit is a secondary backstop. Common optional workflow call/token/deadline settings apply to both architectures; unset settings do not change fixed execution defaults. Planner output ceilings are at most 512 tokens, with the same model used for decisions and quiz generation. Context/token bounds reserve prompt/schema UTF-8 bytes plus output ceilings; provider-reported usage is recorded independently. These conservative bounds are not estimated token metrics.

Deadlines are cooperative: checked before and after nodes and provider calls, with provider operation timeouts clamped to remaining time. In-flight blocking I/O/local work is not forcibly cancelled, so there can be an overrun before the next check. Late completions fail and cannot trigger more actions. PDF extraction retains its separate process timeout. No filesystem/network tools are exposed to model decisions; only local retrieval/generation/validation and the existing approved provider requests are available.

## Metrics, trace, student boundary and comparison

Additive `UsageMetrics` fields count all real model calls, decision/generation calls, actual retriever invocations, generation validation gates/failures, unsuccessful decisions, retries, executed agent nodes, conservative reserved budget, and safe failure code. Offline generation is counted as a generation call but zero model calls. Retry count remains extra quiz-generation attempts; decision failures have a separate counter. Agent usage/cost includes decisions, failed validatable drafts and revisions; transport failures keep usage/cost incomplete/unknown. Evaluation schema checks are shared diagnostics, not separately counted tool invocations.

Each public trace event contains only step, allowlisted action, outcome, duration, and server-owned code. A terminal budget guard may share the last executed step number; it is not an extra executed node. No raw reasons, queries, passages, answers, source IDs or conversations are serialized into traces. Student-safe responses add architecture and this redacted trace while still returning no keys, explanations or citations before submission. The existing bounded attempt store remains the only ephemeral quiz storage.

Benchmark report version 2.0 supports individual modes and paired comparisons using the same versioned synthetic dataset. Paired CLI execution fills missing shared ceilings identically, records effective settings, then restores environment changes. Server requests never mutate global settings. Library callers can supply the common environment settings and inspect `matching_explicit_execution_budgets`. Reports count failures in denominators, retain null unknown metrics, and record actual extra agent work. Fixed runs occur first; graph import/compilation and model stochasticity can affect timings. Record revisions and repeat trials; there is no automatic factual judge or evidence that an agent is better.

The following v0.2.1/v0.2 sections describe the preserved foundation; references to no agents apply to those earlier/default workflows.

# v0.2.1 quality, student attempts, and evaluation

The v0.2 fixed document workflow and provider adapters remain intact. No new dependencies, services, database, authentication, or autonomous tools are introduced.

## Conservative quality validation

`quality.py` centralizes prompt guidance and surface checks. Option keys normalize Unicode, case, spacing, punctuation, and conventional labels, preserving signed/decimal values. Empty normalized options, equivalent options, and common all/none/both/letter-combination options are rejected. Correct answers must exactly match one option. Explanations must be nonempty and cannot contain internal chunk identifiers. Document quizzes reject normalized duplicates and long word sequences at least 90% alike; duplicate rate counts later questions matching any earlier one. Completion templates compare short quoted exercises instead of boilerplate. Legacy multiple-choice quizzes share these checks; the original short-answer demo retains its contract.

Invalid quizzes use the existing bounded retry/usage/cost path. Prompts ask for exactly one supported answer, plausible mutually exclusive distractors, varied concepts, and explanations of why answers are correct. Insufficient or ambiguous material must not be repaired with invented facts. Surface checks cannot prove factual truth, semantic exclusivity, pedagogical quality, or reasoning accuracy. No judge or embeddings are used.

## Student attempt boundary

`attempts.py` provides explicit student-safe/reviewed schemas and a locked store. `POST /api/student/quizzes` and `/api/student/quizzes/pdf` reuse document handlers, copy the validated quiz, shuffle options, retain the key server-side, and serialize a whitelist: question IDs/text/type/options, token/expiry duration, and safe generation/document metadata. No answers, explanations, source excerpts/IDs, or correct flags are returned initially. Existing answer-bearing document and legacy APIs remain available for engineering; the UI never calls them for student attempts.

`POST /api/student/quizzes/submit` receives the token and a complete list of strict integer indices. Validation precedes disclosure. Under the same lock, first submission freezes answers and calculates score against the retained key. Identical retries return the same review; different answers return 409. Reviews include choices, selected/correct choices, explanations, and citations. Scores trust generated keys and are not factual assessments of model outputs.

Limits: 100 attempts, 256 KiB serialized quiz data per attempt, 30-minute monotonic TTL. Expired entries are cleaned on activity; capacity evicts the oldest. No background worker. Responses and stored snapshots do not share mutable state. Restart loses data; multiple workers do not share memory. Use one process for local study. Random bearer tokens provide no account/session identity and travel in POST bodies to avoid access-log URLs. Application logs contain neither tokens nor solutions. Retained quiz data includes cited passages until expiry/eviction, so this is ephemeral storage, not zero in-memory retention. No exam-grade cheating prevention, persistence, cross-process coordination, or public deployment features are provided.

The UI uses radio fieldsets, requires every answer, disables controls during requests, and renders explanations/citations only after successful submission. Provider/document content uses text nodes; no supplied HTML is executed.

## Engineering evaluation

`evaluation/study_cases.v1.json` is an original synthetic CC0 dataset with five stable cases, notes, objectives, and human-review annotations. `python -m app.benchmark --output report.json` explicitly runs the fixed document workflow and writes versioned JSON. Each case supplies its learning objective through the existing topic field, so reasoning/insufficient/ambiguous tasks are explicit generation requests. It defaults to offline and is never triggered by startup/CI. Live providers make paid calls with normal bounded retries; `--case` limits work.

Reports include dataset/code hashes, requested provider/model, Python version, safe capabilities/pricing/limits and document settings, final count/schema/option/duplicate/reference/coverage checks, end-to-end/component timings, reported tokens, retries, cost estimates, and failure/count-success rates. Accepted final questions/citations support manual review of the synthetic dataset. Raw failed outputs and provider exceptions are excluded. Unknown/unobserved values remain null. Failed generation has unavailable quality checks, not a measured duplicate rate of zero. Aggregate cost is null if any case lacks a complete estimate. Structural success on an insufficient/ambiguous case is not a factual pass. Factual grounding always remains `not_evaluated`. A single small run is not a statistical or semantic benchmark.

The fixed workflow, strict schemas, replaceable retrieval, provider metrics, and shared dataset are ready for a controlled v0.3 LangGraph comparison. LangGraph is not implemented here.

# v0.2 document-grounded architecture

The original `/api/exams/generate` endpoint remains intact. The answer-bearing JSON `/api/documents/quiz` and multipart `/api/documents/quiz/pdf` contracts remain available for engineering clients. The browser uses student-safe endpoints described below. Topic/content never appear in query parameters or normal access logs. The release version is 0.2.1.

## Fixed document workflow

Input validation → bounded extraction → normalization/chunking → budgeted lexical retrieval → existing provider adapter → strict multiple-choice/source validation with bounded retries → citations, diagnostics, and usage metrics. No embeddings, vector store, persistence, or agent framework.

- `documents.py`: NFKC/whitespace normalization, character chunks (default 1200 with overlap 200), stable SHA-256-derived IDs, normalized page offsets, empty-content detection, and PDF input limits. Chunks never cross a PDF page boundary; pasted notes have no fabricated page number. IDs are stable for the same normalized content/page/offset and chunk configuration, not persistent upload IDs.
- `pdf_worker.py`: pypdf extraction in a short-lived child process, bytes over pipes, no document writes. It rejects encrypted PDFs, more than 50 pages, and more than 300,000 extracted characters. The parent enforces 5 MiB input and a 15-second process timeout. Linux/Docker additionally caps parser virtual memory at 512 MiB. The child receives no provider keys. Malformed PDFs yield constant safe errors; parser stderr is never forwarded.
- `retrieval.py`: a small replaceable `Retriever` protocol and default lexical implementation. Topic tokens use case-folded words and a small stop-word list; BM25-style scores rank positive matches. Ties follow document order. General selection spreads chunk indices across the document, with middle/extreme priority under tight budgets. Scores are ranking signals, not confidence probabilities; general selection has a null score and explicit coverage reason.
- `document_schemas.py`: additive request/response models and a strict multiple-choice quiz schema. Count is 1–10; topic at most 200 characters. Questions must contain type, options, correct answer, explanation, and 1–3 distinct chunk IDs.
- `grounding.py`: document prompts, retrieval context budgeting, whole-quiz count/schema validation, and server-attached source excerpts. Only IDs present in the actual retrieval result are accepted, even if another ID exists elsewhere in the document. The demo generates literal English word-completion questions and labels its limitations.
- `document_flow.py` and `evaluation.py`: fixed workflow coordination and separate structural/reference/coverage/timing diagnostics.
- `generation.py`: one small optional grounding context reuses the existing provider selection, native-output mode selection, retry/error handling, usage aggregation, cost estimates, and metadata-only logs. Legacy calls take their previous path. `CompletionRequest.source_ids` lets the offline adapter serialize the new demo shape; remote wire adapters remain unchanged.

## Retrieval and context limits

`DOCUMENT_CHUNK_SIZE` accepts 200–3000 characters; overlap must be nonnegative and at most half the size. `DOCUMENT_RETRIEVAL_CHUNKS` defaults to 8 (1–16). `DOCUMENT_CONTEXT_BYTES` defaults to 16000 (1000–32000) and bounds selected passage bytes plus labels. A known provider/model context window further reduces this budget by prompt/schema overhead, the output-token budget, and retry reserve. This is a conservative UTF-8-byte bound, not a tokenizer measurement. If no complete chunk fits, the request fails before generation. Unknown model windows remain unknown; a provider may still reject the configured budget.

Topic queries with no lexical matches fail helpfully. Blank topics select broad coverage. Retrieval is local, deterministic, and replaceable for future experiments. It does not promise semantic recall, synonym matching, or complete document coverage. Chunk overlap can select redundant passages; coverage is explicitly the fraction of document chunk IDs selected, not a factual or page-completeness score. No material is silently truncated inside a selected chunk.

## Validation and evaluation boundary

Every new question is multiple choice with 2–6 distinct options and an answer exactly matching one option. Live output must supply exactly the requested number of questions, and every reference must identify a retrieved chunk. Invalid counts, structures, answers, or source IDs retry through the existing bounded loop, then fail safely; no bad question is skipped. The server attaches citations rather than trusting model-generated source excerpts. The legacy endpoint retains its previous question types and up-to-count behavior.

Evaluation distinguishes:

1. Structural checks: question count, Pydantic schema validity, answer-option consistency.
2. Source checks: citations refer to retrieved IDs; retrieved IDs belong to this document.
3. Coverage: selected IDs / document IDs, and cited retrieved IDs / selected IDs.
4. Timings: preparation (extraction/normalization/chunking), retrieval, and generation workflow excluding retrieval, in milliseconds. Top-level processing time is end-to-end handler time. Provider `metrics.latency_ms` retains whole generation-workflow latency, including retrieval/retries. Timings are rounded and may differ slightly when summed.
5. Actual factual grounding: **not evaluated**. There is no semantic entailment check, human review, LLM judge, or quality benchmark.

A valid source ID proves traceability only. It does not show that the cited passage supports the correct answer or explanation. The deterministic demo is English word completion, not pedagogical generation. Live providers may hallucinate or follow hostile content despite prompt instructions. All passages and topics are treated as untrusted data; no document instruction can execute tools in this application.

## Document handling and security

The legacy JSON body cap remains 512,000 bytes. Only the PDF route permits a 5 MiB file plus 64,000 bytes of multipart overhead; the file is independently capped and options are limited to 2000 characters. Extension, MIME type, PDF header, parse result, page count, and content limits are checked. The normal API validation handler excludes private input values. Multipart may spool to an OS temporary file; it is explicitly closed/deleted on success and failure. The application has no document directory, upload database, or persistent document ID. Student attempts temporarily retain generated quiz data and cited passages.

The PDF child is killable but not a full security sandbox. Windows lacks the Linux process memory cap. Keep parser dependencies current and run untrusted workloads within appropriate OS/container limits; this release introduces no public-deployment infrastructure. No OCR or PDF layout reconstruction is implemented. Mixed documents report skipped empty pages; unusual fonts, tables, columns, and equations may extract poorly.

The UI never sends content to an external provider merely on file selection. It shows explicit cloud/custom/Ollama notices before generation. The existing endpoint allowlists, redirect/proxy restrictions, server-side keys, per-operation timeouts, retry bounds, partial-usage rules, unknown pricing, and unknown total compute cost remain in place. Application logs contain provider metrics only, without topics, notes, uploaded filenames, excerpts, or parser/provider exception details.

Tests use tiny in-memory PDFs and mocked provider transport. Coverage includes extraction limits and errors, metadata/IDs, topic/general retrieval, context bounds, all adapters, unknown/unretrieved IDs, invalid options, retry metrics/costs, evaluation, and legacy behavior. No CI test uses live provider credentials. PDF extraction uses [pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html); it cannot extract text from image-only scans without OCR.

The next agentic comparison can reuse document processing, the retrieval interface, strict quiz contracts, provider adapters, and baseline metrics. Any dynamic decision loop must be introduced and evaluated separately.

# Provider foundation and legacy exam workflow

This independent public lab contains no commercial Ace Studies code, credentials, or customer data. It remains a fixed workflow, without agents, tool execution, LangGraph, or multi-agent orchestration.

## Request flow

Browser → FastAPI input/body validation → server configuration → typed provider adapter → whole-quiz validation → bounded retry → compatible response and metrics.

- `app/schemas.py`: Pydantic requests, questions, strict model-output schema, and metrics.
- `app/providers/config.py`: environment credentials, provider/model defaults, trusted URL policy, per-model capability/pricing profiles, timeout and retry bounds.
- `app/providers/adapters.py`: typed `CompletionRequest`/`CompletionResponse` and `Provider` protocol; small HTTPX REST adapters for OpenAI, Groq, Gemini, Anthropic, Ollama, and an explicitly configured compatible service. The offline adapter wraps the unchanged deterministic pipeline. No hidden SDK retries.
- `app/generation.py`: source extraction, prompts, output-mode selection, validation, retry/backoff, token aggregation, cost estimates, and metadata-only logging.
- `app/main.py`: HTTP contracts and safe error boundaries. `app/llm.py` preserves the old Python helper through the shared workflow.
- `app/index.html`: existing UI with provider/model selection; no keys or browser persistence.

## Contracts and compatibility

`POST /api/exams/generate` retains `text`, `count`, and legacy `mode: offline|openai`. New `provider` supports all seven modes; `mode` and `provider` must agree if both are present. An omitted selection uses `LLM_PROVIDER` (offline by default). `model` overrides that provider's environment default. There is no bundled availability catalog.

Responses retain `architecture`, `mode`, `questions`, `processing_ms`, and `warning`. Questions retain `question`, `answer` (the correct answer), and `source_excerpt`, and add `question_type`, optional `options`, `explanation`, and optional integer `source_reference`.

- Live output must explicitly supply a nonempty question, string answer, supported type, and explanation. Missing fields are not repaired with baseline defaults.
- Multiple-choice answers must exactly match a distinct option; true/false answers must be true or false. Other types cannot contain options.
- The whole quiz must contain 1 through the requested number of questions. Every item is validated; none is skipped or silently truncated. Unknown fields are rejected.
- Source references must exist in the supplied excerpts. The server attaches the actual excerpt and rejects contradictory or unreferenced quotations. References are optional. Schema validation does not prove factual or educational correctness.
- An entire JSON code fence is tolerated. Partial JSON, surrounding prose, refusals, and truncated completions fail validation and may be retried.

The baseline sentence extractor is unchanged: at least seven words and at most 600 characters per sentence. Prompts use the first 40 suitable sentences. This bounded implementation is not full-document retrieval. Demo mode returns up to the requested count of simple passage-based questions.

Failures retain a safe string `detail`, with a stable `code` and generation `metrics` where applicable. HTTP 400 covers configuration, credentials, unsupported features, and upstream request/model rejection; 422 covers request/source validation; 413 covers body size; 502 covers invalid output; 503/504 cover connectivity/unavailability/timeouts. Request-validation responses omit input values and exception contexts.

## Capabilities and fallback

Capabilities belong to an exact `provider:model` profile in `LLM_CAPABILITIES_JSON`. JSON mode, schema mode, tool calling, context window, and token usage default to unknown (`null`). These are operator declarations, not live discoveries or guarantees.

| Adapter | Available output paths | Connectivity check |
| --- | --- | --- |
| Offline | Deterministic JSON serialization | Local, no network |
| OpenAI / Groq / compatible | Prompt JSON, JSON object, JSON schema | GET models |
| Gemini | Prompt JSON, JSON MIME type, JSON schema | GET models |
| Anthropic | Prompt JSON with local validation | GET models |
| Ollama (optional) | Prompt JSON, JSON format, JSON schema | GET api/tags |

`output_mode=auto` uses a declared schema capability when the adapter implements it, then declared JSON mode, otherwise prompt JSON. Explicit native modes fail before the request when support is unknown/false or unimplemented. A rejected native-format request is not silently downgraded; correct the profile or select prompt mode. Tool-calling capability is metadata only in Phase 1. Provider API features do not imply every model supports them.

With a configured context window, a conservative UTF-8-byte bound on prompts/schema plus the output budget rejects overly large requests. This is not tokenizer-measured usage and is never reported as tokens. It may reject inputs an actual tokenizer could fit. No context size is guessed when unknown.

## Bounded execution and observability

Timeout defaults to 30 seconds per HTTP operation (1–120 configurable); health checks use at most 5 seconds without retries. Generation defaults to two additional attempts (0–3 configurable), with 0.25/0.5/1 second backoff. Invalid/incomplete output, malformed API envelopes, transport failures, rate limits, and server errors may be retried. Credential and request/model errors fail immediately. Upstream Retry-After cannot create unbounded waits. HTTPX timeouts bound socket operations, not a global wall-clock deadline.

The output-token budget defaults to 4096 (1–16384). OpenAI/Groq use `max_completion_tokens`, compatible services use `max_tokens`, Gemini uses `maxOutputTokens`, Anthropic uses `max_tokens`, and Ollama uses `num_predict`. Compatible hosts must support this Chat Completions dialect; arbitrary variants are not auto-detected.

Each generation reports provider, requested model, workflow latency including retries, retry count, success, and available provider-reported input/output tokens. Totals include failed validation attempts. Missing usage is null; available partial totals have `usage_complete=false`. Transport failures may incur unreported charges, so subsequent success does not make their usage complete. No token counts are invented. Gemini thinking counts and Anthropic cache input counts are included when reported.

`LLM_PRICING_JSON` optionally supplies USD input/output rates per million tokens for an exact provider/model. Cost is an **estimate** using reported totals, emitted only with configured rates and complete usage. Unknown pricing/usage produces null. Flat rates do not model caching discounts, batch tiers, taxes, or special billing categories. Explicit zero rates describe API charges only. Offline API cost is not applicable; local API cost is unknown unless configured. **Total compute cost remains unknown for all modes**, including local electricity/hardware.

Metrics are returned for successful and handled failed generations and emitted as INFO logs. The app never logs notes, prompts, completions, keys, URLs, or raw provider exceptions. Enable INFO logging if records are wanted; debug HTTP tracing is an operator responsibility. No metrics database is added.

## Security and deployment boundary

- Keys come only from server environment variables. Client key/URL fields are rejected; no browser key storage. Secret-bearing configuration fields are excluded from repr.
- Native cloud endpoints are fixed; SDK-style environment URL overrides are ignored. Custom/Ollama URLs must match explicit server-owned full-URL allowlists. Remote URLs require HTTPS; loopback and explicitly configured Docker-host HTTP are allowed. URL credentials, query strings, fragments, and known metadata endpoints are rejected.
- HTTP clients disable redirects and inherited proxies. Only a trusted administrator may edit allowlists; control DNS and network egress for approved hosts in hosted deployments. This is not a DNS-pinning proxy.
- JSON bodies are capped at 512,000 bytes before parsing, including chunked bodies; the PDF upload exception is described above. Notes accept 60–100,000 characters; counts 1–10; model identifiers have bounded syntax. Upstream responses are capped at 1 MB.
- Docker Compose binds to loopback. There is no authentication, rate limiter, or tenant isolation; add an authenticated, rate-limited gateway and egress policy before public deployment. Connectivity checks are explicit, never run on startup or page load.
- Notes are not durably persisted by this application; Student Mode temporarily retains cited passages in memory as described above. Live providers receive extracted notes and apply their own retention policies. Prompt injection and semantic grounding need further evaluation; citations alone do not solve them.

## Verification and extension

Tests mock HTTPX transport, remove provider environment configuration, and forbid unmocked provider requests. They cover adapters, selection, validation/retries/failures, metrics/costs, redaction, endpoint restrictions, and legacy behavior. CI needs no keys or provider internet access. Mock success does not validate live availability or behavior.

To add a provider, implement the typed adapter, register its endpoint/configuration and output paths, and add transport-contract tests. To use a new model, enter its identifier; declare capabilities/pricing only after checking current documentation.

Provider references: [OpenAI structured output](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat), [Groq structured output](https://console.groq.com/docs/structured-outputs), [Gemini generation](https://ai.google.dev/api/generate-content), [Anthropic Messages](https://platform.claude.com/docs/en/api/messages/create), [Ollama generation](https://docs.ollama.com/api/generate).
