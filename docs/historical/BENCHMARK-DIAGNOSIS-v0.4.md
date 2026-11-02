# v0.4 live Groq benchmark diagnosis

## Finding

The recorded result is **6/15 deterministic completions and 0/15 LLM-agentic completions**, but it does not establish an architecture-quality advantage. Provider/adapter errors affected both workflows. All agentic executions terminated at the three-unsuccessful-decisions guard, which combines retryable provider failures with invalid controller responses under `invalid_decision`. That terminal label is not evidence of fifteen malformed model decisions.

There is also genuine controller-response rejection evidence and one quiz-validation failure. These must remain separate from provider availability. No execution exhausted the shared call/token/deadline budgets. **HTTP 429 is plausible but unconfirmed:** the adapter merges 429 and HTTP 5xx into `unavailable` and does not save upstream statuses or headers.

Only this diagnosis document was added. No architecture, prompt, dataset, validation rule, provider implementation or benchmark output was modified. No live API requests or benchmark reruns were made.

## Evidence and integrity checks

Inspected [raw results](../evaluation/results/v0.4/groq-full/results.json), [execution CSV](../evaluation/results/v0.4/groq-full/executions.csv), [generated report](../evaluation/results/v0.4/groq-full/report.md), saved traces, review artifacts, and the matching local implementation in [benchmark_experiment.py](../app/benchmark_experiment.py), [benchmark.py](../app/benchmark.py), [agent.py](../app/agent.py), [generation.py](../app/generation.py), [adapters.py](../app/providers/adapters.py), [grounding.py](../app/grounding.py) and [execution.py](../app/execution.py).

- All 30 scheduled jobs have one execution, unique job IDs and unique run IDs. Execution order matches the saved schedule, including alternating pair order. No duplicated checkpointed jobs were found.
- CSV execution identities/order, success flags, terminal categories, call counts, retrieval counts and validation counters agree with JSON. CSV blank tokens on partial executions are intentional: JSON retains the partial observations, but the CSV/report excludes incomplete totals.
- The dataset bytes match saved SHA-256 `48a82f066e2329f2a41cb15e5a4ef948ecffd920440d097ba3b8133d9e2bfbcc`.
- Recomputing the runner's complete application-code hash matches `bd22e44d668112a25edca440a5dbff13103349c8d8970bda816ba5905a8616dd`. Code-based interpretations below therefore use the recorded implementation, not an assumed later revision.
- Recorded environment: Python 3.11.9, LangGraph 1.2.14; Groq `openai/gpt-oss-20b`; dataset 1.0; two questions; three generation attempts; 12 total model calls; 100,000 conservative reservation units; 120-second workflow deadline; 24 agent steps; 30-second provider-operation timeout; 4096 quiz output ceiling. Controller output ceiling is `min(512, 4096) = 512`.
- Sampling/seed settings were unspecified; no sampling overrides were sent. Capability fields and pricing were unknown. `auto` therefore selected prompt-based JSON rather than native JSON/schema mode.

## Failure counts

### Terminal categories (mutually exclusive)

| Workflow | Executions | Successful | `unavailable` | `invalid_decision` | Other terminal errors |
|---|---:|---:|---:|---:|---:|
| Deterministic | 15 | 6 (40%) | 9 | 0 | 0 |
| LangGraph LLM-agentic | 15 | 0 (0%) | 0 | 15 | 0 |

`unavailable` at the REST boundary means upstream HTTP **429 or 500–599**. Its application-facing status is set to 503 even for an upstream 429; an application 503 must not be presented as a recorded Groq 503. `invalid_decision` is a local guard with application status 502, not a recorded upstream HTTP status.

### Per-case technical completion and terminal failures

| Synthetic case | Deterministic | Deterministic terminal failures | LLM-agentic | Agentic terminal failures |
|---|---:|---|---:|---|
| `recall-water-cycle` | 1/3 (33.3%) | 2 unavailable | 0/3 | 3 invalid_decision |
| `concept-retrieval-practice` | 1/3 (33.3%) | 2 unavailable | 0/3 | 3 invalid_decision |
| `reasoning-water-budget` | 2/3 (66.7%) | 1 unavailable | 0/3 | 3 invalid_decision |
| `insufficient-factory-output` | 2/3 (66.7%) | 1 unavailable | 0/3 | 3 invalid_decision |
| `ambiguous-lake-temperature` | 0/3 | 3 unavailable | 0/3 | 3 invalid_decision |

These are technical completions, not factual or learning-objective passes. In particular, successful generation for the insufficient-information case does not verify that its objective was met. Human factual review remains unevaluated.

### Underlying events (overlapping, not terminal-category counts)

| Evidence | Deterministic | LLM-agentic |
|---|---|---|
| Provider/adapter error evidence | All 9 failed executions; also 3 successful executions recovered after retries | All 15 executions: 14 have explicit decision-provider errors; the remaining execution has a generation-provider error |
| Explicit nonterminal `decision_provider_error` trace events | Not applicable | 27 events in 14 executions |
| Explicit `invalid_action_or_arguments` events | Not applicable | 3 events across 2 executions, both recall cases |
| Terminal third unsuccessful decision with underlying cause erased | Not applicable | 15 events |
| Quiz validation failures | 1 event in ambiguous repetition 3 | 0 events; validation was never invoked |
| Retrieval failures | None observed | None observed; all 10 invoked retrievals succeeded |
| Call/token/workflow deadline/step exhaustion | None recorded | None recorded |

The 15 erased terminal decision causes must not be counted automatically as either provider failures or malformed responses. `bad_decision()` raises on the third failure before returning its original feedback code. The traces preserve `invalid_decision` instead. The failure counter is cumulative across the execution; intervening valid decisions do not reset it.

## Earliest meaningful event for every execution

Rows follow JSON/CSV order. Run prefixes are unique in these artifacts; complete IDs remain in the linked files. `D` means deterministic; `A` means agentic. `P` means a retryable provider/adapter exception whose exact early category/status is not retained. An `unavailable` terminal is specifically the 429-or-5xx mapping. Success rows show recovered errors where applicable.

| # | Run prefix | Case / repetition | Workflow | Earliest meaningful failure or recovery evidence | Terminal result |
|---:|---|---|:---:|---|---|
| 1 | `24f41b06` | recall / 1 | D | None recorded; first generation validated | Success |
| 2 | `8e82192d` | recall / 1 | A | Step 5: invalid controller response/action/arguments, after retrieval and first generation | invalid_decision, step 11 |
| 3 | `fb520b2e` | recall / 2 | A | Step 1: decision_provider_error; step 2 also rejects response/action/arguments | invalid_decision, step 3 |
| 4 | `de5e1bd5` | recall / 2 | D | Attempt 1: P; three calls, no validation; exact early status unknown | unavailable |
| 5 | `277a2c5b` | recall / 3 | D | Attempt 1: P; three calls, no validation | unavailable |
| 6 | `9aadedb5` | recall / 3 | A | Step 3: decision_provider_error after successful retrieval | invalid_decision, step 5 |
| 7 | `9885ad77` | concept / 1 | A | Step 3: decision_provider_error after successful retrieval | invalid_decision, step 5 |
| 8 | `8bbe9d5b` | concept / 1 | D | Attempt 1: P; two provider/adapter errors before the single validated response | Success on attempt 3 |
| 9 | `9e4961c3` | concept / 2 | D | Attempt 1: P; three calls, no validation | unavailable |
| 10 | `2f423f42` | concept / 2 | A | Step 3: decision_provider_error after successful retrieval | invalid_decision, step 5 |
| 11 | `6544fd87` | concept / 3 | A | Step 1: decision_provider_error; retrieval later succeeds | invalid_decision, step 5 |
| 12 | `038cd906` | concept / 3 | D | Attempt 1: P; three calls, no validation | unavailable |
| 13 | `705531c9` | reasoning / 1 | D | None recorded; first generation validated | Success |
| 14 | `99fc188d` | reasoning / 1 | A | Step 1: decision_provider_error; no retrieval | invalid_decision, step 3 |
| 15 | `dc6ef5b8` | reasoning / 2 | A | Step 3: decision_provider_error after successful retrieval | invalid_decision, step 5 |
| 16 | `313bef1e` | reasoning / 2 | D | Attempt 1: P; one provider/adapter error before validation | Success on attempt 2 |
| 17 | `7464f16d` | reasoning / 3 | D | Attempt 1: P; three calls, no validation | unavailable |
| 18 | `0548d1af` | reasoning / 3 | A | Step 3: decision_provider_error after successful retrieval | invalid_decision, step 5 |
| 19 | `e27cf196` | insufficient / 1 | A | Step 3: decision_provider_error after successful retrieval | invalid_decision, step 5 |
| 20 | `965fb11e` | insufficient / 1 | D | Attempt 1: P; three calls, no validation | unavailable |
| 21 | `ebbfe9b1` | insufficient / 2 | D | None recorded; first generation validated | Success |
| 22 | `ed836dc2` | insufficient / 2 | A | Step 1: decision_provider_error; no retrieval | invalid_decision, step 3 |
| 23 | `d4d482ed` | insufficient / 3 | A | Step 3: decision_provider_error after successful retrieval | invalid_decision, step 5 |
| 24 | `e39e34e5` | insufficient / 3 | D | Attempt 1: P; two provider/adapter errors before validation | Success on attempt 3 |
| 25 | `cda6c0ce` | ambiguous / 1 | D | Attempt 1: P; three calls, no validation | unavailable |
| 26 | `f37b8222` | ambiguous / 1 | A | Step 1: decision_provider_error; retrieval later succeeds | invalid_decision, step 5 |
| 27 | `92424698` | ambiguous / 2 | A | Step 1: decision_provider_error; no retrieval | invalid_decision, step 3 |
| 28 | `e9f6c94a` | ambiguous / 2 | D | Attempt 1: P; three calls, no validation | unavailable |
| 29 | `1b11b9de` | ambiguous / 3 | D | Attempt 1: P; reconstructed attempt 2 validation failure; attempt 3 unavailable | unavailable |
| 30 | `48cf47eb` | ambiguous / 3 | A | Step 1: decision_provider_error; no retrieval | invalid_decision, step 3 |

Deterministic attempt ordering is inferred from the matching implementation and counters, not a saved per-attempt trace. In the eight failed runs with zero validation calls, all three attempts failed before validation. Their first error could be unavailable, timeout, connection, or another retryable adapter error; only the last category survives.

For execution 29, the same case's unmodified three-call reservation is 24,402 units. Its recorded reservation is 24,625: exactly **223 additional UTF-8 bytes**, the fixed validation-feedback suffix. The suffix is appended after invalid output and applies to later requests. With three attempted calls and one validation failure, one suffix-bearing call means validation failed on attempt 2; attempt 1 failed at the provider/adapter boundary and attempt 3 ended unavailable. This is an implementation-supported reconstruction, not a recovered raw completion. The exact validation defect remains unknown.

## Root causes by layer

### Provider/adapter boundary: strong evidence; upstream condition unresolved

All nine deterministic terminal failures passed through the adapter's HTTP 429-or-5xx branch. Eight never reached validation. The ninth mixed provider failure with one invalid/incomplete quiz. Three successful deterministic executions required retries without any validation failures, demonstrating transient provider/adapter failures even among completions.

Of 38 deterministic calls, only seven reached validation (six accepted, one rejected). The remaining 31 failed before that gate, consistent with retryable provider/adapter exceptions in this implementation. Only nine terminal exceptions retain the specific `unavailable` category; earlier categories are lost. This is not evidence that all 31 were 429.

Agent traces explicitly report 27 retryable decision-provider errors and one retryable generation-provider error. A decision-provider error can include unavailable, connection, timeout or response parsing errors. The agent discards that underlying code before recording the trace. The data support provider/adapter disruption throughout the run, but not a single verified upstream cause for every request.

### Controller/orchestration: error attribution loss plus limited response-rejection evidence

There were 58 controller calls: 13 accepted decisions, three explicit response/action rejections, 27 explicit provider errors, and 15 terminal unsuccessful decisions with hidden subcause. Those counts sum to 58. Ten executions retrieved successfully; five stopped before retrieval. Only execution 2 reached quiz generation. No execution reached a `validate` or `finish` node.

Execution 2 is distinct: retrieve succeeded, generation returned twice, controller responses were rejected at steps 5 and 8, and a third generation attempt had a provider error. It then hit the decision guard. `generate/ok` means the call returned, **not** that the quiz was complete or valid. The controller chose more generation instead of reaching validation; the unretained controller payloads prevent determining why the rejected decisions failed.

Execution 3 has both a provider failure and an explicit invalid response. Its controller ledger records 512 output tokens, exactly the controller ceiling. Truncation/incomplete output is a plausible hypothesis because the adapter accepts only `finish_reason == stop` as complete, and the controller rejects incomplete responses. However, the finish reason, content, reasoning-token split and individual response usage are absent. A ceiling hit does not prove truncation, and this hypothesis cannot explain all fifteen agent failures.

The cumulative three-failure guard also counts transient provider errors, and controller retries have no deliberate backoff. Consequently provider disruption can rapidly become a local `invalid_decision` failure without three invalid model outputs. This is existing orchestration behavior, not a benchmark scheduling exception. It is a diagnostic limitation and a potential rate-limit amplifier, not proof that the graph is broken.

### Quiz generation/validation: one confirmed rejection, mostly untested agent output

There is exactly one observed quiz-validation failure: deterministic ambiguous repetition 3. The stored data cannot distinguish JSON/schema, count, option, duplicate, source-reference, or incomplete-output rejection. The failed raw candidate and validation subreason were deliberately not retained.

Agentic validation failures equal zero because validation calls equal zero. This is **not** a 100% agent quiz-validity result. Two returned agent candidates were never validated. Neither successful technical validation nor citation validity verifies factual support.

### Execution budgets/deadlines: no evidence of exhaustion

Maximum observed model calls were 3 deterministic and 10 agentic, below 12. Maximum reserved budgets were 24,625 and 48,604, below 100,000. Agent steps peaked at 11, below 24. Maximum end-to-end latency was 12.284 seconds, below 120 seconds. No terminal call-limit, token-budget, step-limit or workflow-timeout error is present. Hidden earlier retryable provider timeouts cannot be excluded, but there is no evidence of a workflow deadline causing these outcomes. Raising the shared budgets would not address the demonstrated failure paths.

## Rate-limit investigation and pacing

**No upstream HTTP statuses, Retry-After values, request IDs, rate-limit limits/remaining/reset headers, per-request timestamps, finish reasons or raw provider error bodies are stored in these artifacts.** There are no separate live response/log artifacts in the inspected repository. The REST adapter checks status before consuming a failure body and exports neither status nor headers. Thus the investigation cannot verify whether Groq actually returned 429, which quota bucket was involved, or whether a 5xx incident occurred instead.

The two-second delay is between whole executions only. It is not between provider requests. Deterministic retries sleep only 0.25 and 0.5 seconds; controller failures can immediately trigger another decision call. The first agentic execution issued ten calls in approximately 10.82 seconds of workflow time. Across the run there were **99 attempted model calls: 38 deterministic, 58 controller and three agentic generation calls**. Shared ceilings are per execution and do not coordinate account-wide rolling request/token quotas.

Recorded partial usage sums to **28,720 tokens** (15,896 input and 12,824 output). This is an observed subtotal, not complete consumption or a provider-billed estimate: only three executions have complete usage; every agentic execution has incomplete usage. Reserved byte/output bounds must not be substituted for tokenizer-measured or provider rate-accounted consumption.

Summed end-to-end execution latencies are 88.248 seconds. An uninterrupted schedule adds at least 58 seconds of configured inter-execution sleep, yielding approximately 146.248 seconds before artifact overhead and other gaps. Ignoring that overhead gives about 40.6 attempted calls/minute and 11.8k *recorded* tokens/minute. These are illustrative workload calculations, not measured rolling-window rates or actual quota usage: request timestamps, actual wall-clock duration, interruptions, unreported usage and other account traffic are unknown.

**Conclusion:** two seconds did not prevent widespread provider/adapter failures, and it provides no protection against within-execution bursts. It is insufficient as a verified rate-control mechanism. The artifacts do not establish that it violated a particular Groq quota. No defensible numeric request delay can be calibrated from this run alone.

After obtaining actual account/model quota data, a starting per-request spacing calculation is `max(60/R, 60*T/Q)` seconds, where `R` is the permitted requests/minute, `Q` the applicable tokens/minute and `T` a conservatively measured per-request token allowance. Apply additional headroom and all applicable longer-window limits; respect observed Retry-After/reset values. This average-spacing formula is not a guarantee for rolling buckets, varying request sizes, provider reservation policies or concurrent account traffic. None of R, Q or a complete T is available here. Do not fill them with invented public/free-tier values.

## Fairness and benchmark-only configuration

| Control | Verification |
|---|---|
| Source documents/objectives | Same bundled dataset and verified hash; runner selects the same case text/topic by case ID for both workflows |
| Question count | All 30 requested counts are two; all six accepted quizzes contain two questions |
| Provider/model | All execution and top-level metric identities are Groq / openai/gpt-oss-20b; called controller/generator components agree |
| Generation services | Both use GroundingContext prompt rendering, GroundedQuiz schema, shared quality/source validator and Groq adapter |
| Retrieval | Same LexicalRetriever and chunk/context settings: 1200/200 characters, 16,000 context bytes, eight chunks; agent queries/subsets can differ |
| Generation attempts | Shared retries=2, hence three attempted generations, including provider failures; observed deterministic attempts 1–3, agentic 0–3 |
| Total budgets | Same 12-call, 100,000-unit and 120-second ceilings; none exhausted |
| Sampling/output mode | Same unspecified sampling and prompt-mode JSON; generator ceiling 4096; controller ceiling 512 is an intentional existing difference |
| Order/pacing | Saved alternating schedule followed; sequential execution and two-second inter-execution delay; no request-level quota coordination |
| Jev/offline fixture | Live transport selected, LLM controller throughout; no Jev calls or scripted offline transport evidence |

Call accounting is internally consistent in all 30 executions: total model calls equal decision plus generation calls, and equal the two component call counters. Agent trace decide/generate events agree with those counts. Failed attempted requests are counted, as intended; counters cannot prove upstream acceptance/billing without request logs. Local retrieval is counted separately and consumes no provider model call.

No benchmark-only change is supported as the direct cause: code/dataset hashes match, the runner calls the shared workflow with the intended count/model, and observed budgets have ample headroom. Experimental *conditions* can still matter: five cases repeated in a sustained sequence create a different quota/load context than an isolated successful smoke. Equal budgets/attempt limits do not equalize request counts, retry handling or provider exposure; agentic work requires multiple successful controller calls. Alternating order cannot remove shared quota carryover, cumulative throttling or provider load.

## Comparison with the previous successful live agent

The supplied earlier observation reports a successful agentic run at 6.32 seconds, four controller calls plus one generation call, zero retries and 6,798 reported tokens. Its trace/configuration artifact was not found among repository JSON results. It demonstrates that a successful live observation was reported, not that its source, capabilities, output ceilings, sampling, account quota state or pinned model revision matched this experiment.

Here, only the first agentic execution got as far as generation, using seven controller calls plus three generation attempts without validation. Fourteen later executions never generated. The contrast is consistent with a combination of provider pressure and occasional controller-response problems, rather than uniformly poor generated quizzes. Without the earlier raw artifact or current per-request responses, the difference cannot be assigned causally to Groq quotas, a model revision or the 512-token ceiling.

## Missing information and uncertainties

1. Upstream statuses/headers and quota/account traffic: cannot distinguish confirmed throttling from server errors or calibrate pacing.
2. Underlying errors on the third unsuccessful decision and on earlier deterministic attempts: terminal labels erase causal history.
3. Controller finish reason, safe parse/precondition subreason, per-call usage and reasoning-token split: cannot identify truncation versus malformed JSON versus invalid actions/arguments.
4. Failed quiz validation subreason and candidate: cannot identify the one deterministic validation defect or judge unvalidated agent candidates.
5. Per-request and execution timestamps/resume gaps: aggregate durations do not establish rolling rates or verify actual sleeps.
6. Returned/pinned model revision and prior successful live trace/configuration: alias/configuration comparisons remain incomplete.
7. Human review: accepted answers and explanations remain unverified; rejected output is absent. Unknown pricing remains unknown.

## Minimal corrective actions to consider next

These are proposals, **not changes made during diagnosis**.

1. Add a small safe per-attempt diagnostic record: workflow/component, request sequence, timestamps/duration, upstream HTTP status, allowlisted Retry-After/rate-limit fields, finish reason, per-call reported usage and underlying constant error code. Exclude authorization, prompts, response bodies and arbitrary headers. Preserve subcause on the terminal decision guard and deterministic retry history.
2. Once actual quota/reset information is available, coordinate pacing across every provider request, including controller calls and generation retries. Honor server wait guidance with bounded waits/backoff. Record infrastructure errors separately from model-decision errors even if the existing guard remains unchanged.
3. Add finite local failure subreasons for incomplete completion, JSON/schema failure and action/precondition rejection; likewise distinguish quiz-validation categories. This can diagnose without storing raw failed content or weakening validation.
4. Investigate the 512-token controller-cap hypothesis only if finish reasons/usage support it. Do not increase caps, change prompts, enable a different output mode or relax validation as an unlabelled fix. Any such later change is a separate experimental condition.
5. Keep the present results immutable and retain them as a provider-disrupted pilot. Do not replace failed runs with selected successful retries or interpret current latency/token summaries as successful-task architecture performance.

## Small verification rerun recommendation

Do not rerun the full pilot yet. After the diagnostic-only instrumentation and quota check above, use the existing smoke schedule on **recall-water-cycle**, one deterministic and one LLM-agentic execution, sequentially, with the same two questions, generation model, prompts, validators, attempt limits and execution budgets. Use a fresh output directory. Retain the original 512-token controller cap for this diagnostic baseline. Add request-level pacing derived from observed headers/actual quota rather than guessing an inter-run delay. Stop for investigation if unavailable responses recur; wait for the reported reset instead of repeatedly consuming guards.

The existing CLI shape is `python -m app.benchmark --mode smoke --provider groq --model openai/gpt-oss-20b --allow-live --env-file .env --case recall-water-cycle --count 2 --generation-attempts 3 --max-model-calls 12 --token-budget 100000 --timeout 120 --output-dir evaluation/results/v0.4/groq-diagnostic-smoke`. **Not executed here.** The current CLI's `--delay` still controls whole executions only; this command alone does not add the proposed request-level diagnostics/pacing.

Verify individual provider responses and stage progression: accepted retrieve decision, successful retrieval, accepted generate decision, returned candidate, accepted validate decision, deterministic validation and accepted finish with final gate. Reconcile every attempted request to counters and preserve all failures. If the first pair is provider-clean, at most one additional pair in reversed workflow order can check recurrence/order effects using the existing custom mode, without making benchmark claims. A separate ambiguous-case pair is appropriate only after the basic path works and the earlier validation subcause is observable. The original full data remain unchanged; no selective rerun is merged into their denominators.

Only if provider-clean failures consistently show incomplete controller completions at the cap should a separately labelled, one-variable controller-ceiling experiment be proposed. A small verification establishes functionality and diagnostic adequacy, not a statistical speed, cost or quality advantage.
