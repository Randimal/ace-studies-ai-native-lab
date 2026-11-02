# v0.4 controlled architecture benchmarking

## v0.4.1 reliability and diagnostics

Pilot 1 is the original immutable 30-execution run at `evaluation/results/v0.4/groq-full/`. Its [diagnosis](BENCHMARK-DIAGNOSIS-v0.4.md) remains historical evidence. The benchmark CLI refuses writes there, including report/review regeneration. Use a fresh directory for v0.4.1; do not merge selective successful retries into Pilot 1 or infer upstream statuses that were never saved.

New safe request diagnostics are enabled for actual provider attempts in normal execution metrics as additive fields. Pacing is **optional and benchmark-only**. Prompts, retrieval, schemas, validation rules, model/controller selection, retry/attempt limits, graph behavior and the 512-token controller output ceiling are unchanged. Required error handling preserves the underlying provider cause at the existing cumulative decision-failure guard. There is no fallback.

### Pacing options

| Option | Behavior |
|---|---|
| `--request-pacing` | Enables shared request-level retry/reset guidance handling without assuming quotas |
| `--request-rpm R` | Positive finite requests/minute; enables shared smooth request-start spacing of at least 60/R seconds |
| `--request-tpm T` | Positive finite units/minute; enables a rolling 60-second conservative token reservation ledger |
| `--max-request-wait S` | Maximum deliberate wait per attempted request, default 30 seconds, range (0,120]; workflow deadline also applies |
| `--delay S` | Existing inter-execution delay only; separate from request pacing |

The same pacer instance covers all executions, deterministic generation, LLM controller decisions, agent generation and retries. It reserves prompt/schema UTF-8 bytes plus the requested output ceiling, using the same conservative bound as execution budgets. These units are **not reported/billed tokens** and can overestimate true consumption substantially. Failed requests retain reservations conservatively. A request larger than the configured TPM allowance fails before sending (`pacing_capacity`). If the required wait exceeds the bound, it fails before sending (`pacing_wait_limit`); the limiter never clips a long server wait and sends early. Waiting can exhaust the unchanged workflow deadline (`workflow_timeout`), and unsent calls do not increment model-call counters.

Check the actual provider console for your account/project/model limits, including RPM, TPM, daily caps and shared account traffic. Choose conservative values below available capacity with headroom. Do not copy guessed free-tier limits. New allowlisted `limit_requests`/`limit_tokens` fields can help interpret observed responses, but the runner does not automatically assume they describe every quota window. Verify the provider's meaning and account scope. No live discovery request is made.

Valid Retry-After numeric delays or HTTP dates and parsed reset guidance create cooldowns. Supported reset forms are duration strings such as `1m2.5s`, numeric seconds, numeric Unix-epoch timestamps and HTTP dates. Reset guidance is honored on 429, or when a corresponding remaining count is zero. Malformed/missing fields remain unknown. On 429 without valid guidance, enabled pacing uses exponential 1/2/4/.../128-second retry backoff, still subject to the configured wait bound; this is a backoff policy, **not a provider quota**. Header-only pacing cannot prevent an initial 429 and cannot guarantee quota compliance. Existing bounded deterministic retry backoff remains; controller feedback/guards are unchanged.

The pacer is process-local and intended for one sequential benchmark writer. Recent checkpointed reservations, global request sequences and cooldowns are restored on resume. Uncheckpointed in-flight work and other clients are unknown; wait for actual provider reset before resuming after an interruption if necessary. No token/call/deadline budgets are silently increased to accommodate pacing.

### Two-execution diagnostic smoke (not executed)

After explicit operator approval, this command uses one synthetic case and both workflows, preserving Pilot 1's generation configuration. It enables header-guided pacing without claiming knowledge of account quotas. Append `--request-rpm` and/or `--request-tpm` with your verified conservative values if available.

```bash
python -m app.benchmark --mode smoke --provider groq --model openai/gpt-oss-20b --allow-live --env-file .env --case recall-water-cycle --count 2 --generation-attempts 3 --max-model-calls 12 --token-budget 100000 --timeout 120 --delay 2 --request-pacing --max-request-wait 30 --output-dir evaluation/results/v0.4.1/groq-diagnostic-smoke
```

No live benchmark is part of implementation, startup, tests or Docker verification. Calls/retries may incur charges. Inspect one diagnostic pair before considering additional experiments. A smoke result establishes neither statistical superiority nor factual accuracy.

### Interpreting diagnostics

Each `metrics.provider_attempts` entry contains execution-local sequence, benchmark-global sequence/reserved units when pacing is enabled, component, UTC start, duration, actual upstream HTTP status when available, parsed retry/reset/remaining/limit data, allowlisted finish reason, output-complete flag, reported tokens, provider-success flag, constant error code and output status. Missing HTTP/completion data stay null. New diagnostic fields never include credentials, URLs, prompts, documents, model-response text, raw error bodies or arbitrary headers. Existing accepted-question exports are separate human-review artifacts.

| Fine category | Meaning |
|---|---|
| `provider_rate_limit` | Actual upstream 429 observed |
| `provider_server_error` | Actual upstream 5xx observed |
| `connection` / `timeout` | Network failure / provider-operation timeout; upstream status may be absent |
| `provider_response`, `provider_request`, `credentials`, etc. | Existing safe adapter categories, retained independently of model output quality |
| `controller_incomplete_output` | Controller completion was incomplete, including truncation |
| `controller_invalid_structure` | Complete controller response failed JSON/schema checks |
| `controller_unsupported_action` | Named action is outside the existing action vocabulary |
| `controller_invalid_precondition` | Known action/arguments failed the existing state/evidence/precondition checks |
| `quiz_validation_failure` | Quiz failed the unchanged completeness/schema/count/quality/source gate |
| `pacing_capacity` / `pacing_wait_limit` | Request cannot fit configured TPM / required wait cannot fit configured pacing bound |

For API compatibility, the existing outward `unavailable` code/status still covers 429/5xx. `underlying_terminal_error` and benchmark `error_category` provide the distinction, while raw `failure_code` preserves the compatibility code. Output-related decision guards can retain `invalid_decision` externally with the precise underlying output category. Provider-triggered guard termination re-raises the actual provider exception instead. `termination_reason=decision_failure_limit` identifies this unchanged guard. The historical `decision_failures` counter remains the cumulative unsuccessful-decision count; use `controller_output_failures` to measure rejected model outputs.

JSON retains per-attempt history including failures recovered by later success. CSV/Markdown add 429/5xx/other-provider failure counts, controller-output failures, returned/failed provider attempts, accepted/rejected/unassessed output attempts, pacing wait and terminal subcause. A provider-successful attempt means the adapter returned a response, even if incomplete/invalid; it is not a valid quiz or factual pass. Agent candidates not validated remain unassessed. Legacy reports without diagnostics show null, never invented zero events.

`end_to_end_latency_ms` / CSV `benchmark_wall_clock_ms` measure per-execution wall-clock including local graph work, request pacing and existing retry backoff. `pacing_wait_ms` meters the deliberate request-level wait; `provider_execution_ms` sums adapter invocation/response processing time excluding pacing. `inter_execution_wait_ms` is recorded separately. Provider component latencies also exclude request pacing. Artifact-export time is outside execution latency. Report throttling separately from model-quality failures: an HTTP 429 supplies no evidence that a model chose an invalid action or wrote a bad quiz. Human factual quality remains a separate assessment.

### v0.4.1 offline verification

```bash
python -m pytest -q
docker build -t ace-studies-ai-native-lab:v0.4.1 .
docker build -f tests/Dockerfile -t ace-studies-ai-native-lab:v0.4.1-test .
docker run --rm --network none ace-studies-ai-native-lab:v0.4.1-test
docker run --rm --network none ace-studies-ai-native-lab:v0.4.1 python -m app.benchmark --mode smoke --delay 0 --request-pacing --output-dir /tmp/v041-smoke
```

The commands below describe the existing v0.4 protocol; use new v0.4.1 output directories for subsequent work. Historical data retain their original interpretation.

Use the existing `app.benchmark` entry point. No command is launched by startup or CI. Run in the installed local Python environment. Live calls require `--allow-live`, including legacy `--output` benchmark commands. Jev remains available only through the legacy opt-in runner and is excluded from these pilots.

```bash
# 1. Offline paired smoke: one synthetic case, two sequential executions.
python -m app.benchmark --mode smoke --delay 0 --output-dir evaluation/results/v0.4/offline-smoke

# 2. Explicit live Groq paired smoke: same generation model/settings.
python -m app.benchmark --mode smoke --provider groq --model openai/gpt-oss-20b --allow-live --env-file .env --count 2 --generation-attempts 3 --max-model-calls 12 --token-budget 100000 --timeout 120 --delay 2 --output-dir evaluation/results/v0.4/groq-smoke

# 3. Full Groq pilot: five cases x three repetitions x two workflows = 30.
python -m app.benchmark --mode full --provider groq --model openai/gpt-oss-20b --allow-live --env-file .env --count 2 --generation-attempts 3 --max-model-calls 12 --token-budget 100000 --timeout 120 --delay 2 --output-dir evaluation/results/v0.4.1/groq-pilot2

# Resume: repeat the exact command with --resume. Do not change code/settings.
# 4. Export/re-export a fresh blind template (overwrites the template only).
python -m app.benchmark --mode export-review --output-dir evaluation/results/v0.4.1/groq-pilot2

# 5. Report from saved results; no provider calls, with optional scored reviews.
python -m app.benchmark --mode report --output-dir evaluation/results/v0.4.1/groq-pilot2 --reviews evaluation/results/v0.4.1/groq-pilot2/review-scored.csv
# Omit --reviews to explicitly report factual quality as not_evaluated.
```

Use an accessible model identifier; the example is not an availability promise. Shell variables override `--env-file`. Secrets, endpoints and environment files are never exported. Dataset version defaults to `1.0` and only the bundled synthetic dataset is accepted. No files are uploaded automatically. Fixed question count defaults to two. Smoke always pairs deterministic/LLM-agentic on one case; full always pairs them across all five cases with three repetitions. `--mode custom --workflow deterministic|agentic|both --repetitions N --case ID` supports other controlled configurations. `--max-agent-steps` and `--max-output-tokens` expose the remaining bounds. All executions are sequential; successive pairs reverse workflow order, including across case boundaries.

Optional Groq `--temperature 0.2 --top-p 0.9 --seed 42` values are sent to both quiz generation and LLM control calls. Model support can vary: unsupported fields may be rejected by the provider and recorded as failures. Other adapters preserve their defaults and record requested sampling/seed fields as unsupported. No seed promises deterministic provider execution. Unspecified sampling uses provider defaults, recorded as unspecified rather than invented values. Pin model revisions when possible.

The default two-second inter-execution delay is modest pacing, not a quota guarantee. Expected limits include requests/minute and tokens/minute or daily limits, varying by model/account. Check your provider console before running. Agent controller calls and generation retries also consume quotas within an execution. Existing adapters map HTTP 429 and server errors to safe `unavailable` failures; bounded workflow retry/decision handling remains unchanged. The runner records failures and never retries a whole execution. Budget exhaustion records `token_budget`, `model_call_limit`, `workflow_timeout`, `generation_limit` or `agent_step_limit` as applicable. Increase delay or reduce scope if quotas are insufficient. Calls/retries can incur API charges; configure `LLM_PRICING_JSON` for estimates. Unknown pricing stays null, never zero.

Each directory contains `results.json` (sanitized full configuration, dataset/code hashes, schedule, per-execution UUIDs, questions and traces), `executions.csv`, `review-template.csv`, `review-key.json`, and `report.md`. JSON is atomically replaced and flushed after each execution before derived artifacts are exported. Resume validates the complete configuration, code, dataset, schedule and completed job identities, including failed executions. One writer per output directory is required. If interrupted during a provider request before its checkpoint, that uncompleted job can run again and incur charges; already checkpointed jobs never run again. Use a new directory for a changed experiment. Report/export commands make no network calls. Report/export can recover derived artifacts from a partial run. The report shows completed/planned counts.

Offline smoke uses a benchmark-only scripted Groq-shaped transport with no real credentials, no network and no reported tokens/costs. It runs the real deterministic workflow and LangGraph with shared demo-generated quiz fixtures. Its agent decisions are scripted; its timing, counts and outputs are plumbing evidence only, never model performance or factual-quality evidence. The application still rejects offline agentic user requests.

## Blind human review

Give reviewers **only** `review-template.csv`, copied to `review-scored.csv`. Keep raw results, report and `review-key.json` with the analyst: the key joins random blind run IDs to execution UUIDs and architectures. Reviewer rows are ordered by random question identity, not architecture or execution order. Wording may still reveal architecture; blinding is not guaranteed. Each row includes question, choices, generated selected answer, explanation, and referenced source excerpts. Case IDs are visible. No workflow, controller or chronological run ID is included.

Score every dimension from 0 to 2, or leave all five blank for an unreviewed question. Completed rows must have all five scores; partial/invalid scores and unknown/duplicate review IDs are rejected. Use one consensus review per question; multiple-rater analysis is outside v0.4. Preserve review IDs. Optionally fill reviewer and notes. Reporting joins only by review ID; it never trusts reviewer-supplied architecture labels.

| CSV dimension | 0 | 1 | 2 |
|---|---|---|---|
| answer_supported | Source contradicts or does not support selected answer | Partial or ambiguous support | Source clearly supports the selected answer |
| explanation_consistent | Contradicts answer/source | Incomplete or partly inconsistent | Consistent with both answer and source |
| question_clear | Ambiguous or unanswerable | Minor clarity issue | Clear and unambiguous |
| distractors_plausible_distinct | Implausible, overlapping, or multiple correct choices | Some weak distractors | Plausible, distinct, clearly incorrect alternatives |
| attribution_appropriate | Missing or unrelated passage | Partly relevant or incomplete attribution | Relevant passages adequately support attribution |

Review insufficient-information and ambiguous-source cases against their sources, without supplying missing facts from outside knowledge. The generated answer key is a proposed answer, not a verified answer. Technical schema/citation validation proves structure and traceability only. Human results show reviewed counts, eligible question count and dimension means per architecture; blank/unavailable reviews remain `not_evaluated`. Copy scored files before re-exporting templates; benchmark resume/report never overwrites reviewer files.

## Interpreting evidence

Report denominators include failures. Schema/reference/duplicate/coverage values are null when no accepted quiz exists. Retry and validation-failure execution rates use measured counters; the per-check validation failure rate has a separate denominator. Reported-token medians omit incomplete usage and show observation counts. Known-cost subtotals are separate from unknown-cost counts and total cost is null unless every execution has an estimate. Component latency is provider/parse timing, not the full graph-node duration; end-to-end latency includes processing, graph compilation and validation.

Median and nearest-rank P95 are descriptive. With one smoke observation or fifteen full observations per architecture, P95 is unstable and often the maximum. Five synthetic cases do not represent curricula; repeats on shared sources are not independent tasks. Agent-selected retrieval queries, evidence, decisions and revisions can differ despite shared source documents, retrieval implementation, quiz prompt, model and generation settings. Matching total budgets does not imply matching call counts. No chart, significance test, causal advantage or factual correctness is inferred automatically.

The supplied initial Groq observations (8.99s/3 generation calls/2 retries/8,461 tokens versus 6.32s/4 controller + 1 generation calls/0 retries/6,798 tokens, both successful) are single observations only. They are motivation for this protocol, not generalizable findings. No live pilot was run during v0.4 implementation.

## Offline verification

```bash
python -m pytest -q
docker build -t ace-studies-ai-native-lab:v0.4 .
docker build -f tests/Dockerfile --build-arg APP_IMAGE=ace-studies-ai-native-lab:v0.4 -t ace-studies-ai-native-lab:v0.4-test .
docker run --rm --network none ace-studies-ai-native-lab:v0.4-test
docker run --rm --network none ace-studies-ai-native-lab:v0.4 python -m app.benchmark --mode smoke --delay 0 --output-dir /tmp/v04-smoke
```

Image builds install dependencies; test execution and smoke need no provider network. The included [offline sample report](../evaluation/results/v0.4/offline-smoke/report.md) has two successful scripted executions with unknown reported tokens/costs and unevaluated factual quality. Its local timings are not model benchmarks.
