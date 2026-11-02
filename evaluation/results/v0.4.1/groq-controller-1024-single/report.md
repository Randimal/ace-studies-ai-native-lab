# Controlled architecture benchmark

Mode: custom; transport: live. Completed 1/1 executions.

## Measurements

P95 uses nearest rank. With 1–15 observations per architecture it is unstable and often the maximum. Token medians include only complete reported usage. Latencies include failures. End-to-end benchmark wall-clock latency includes request pacing, local work and retry backoff; inter-execution waits are separate. Provider execution time excludes deliberate pacing. Provider-successful attempts mean returned responses, not validated or factual answers. Output attempts may be accepted, rejected or unassessed. Historical diagnostics are unknown, never reconstructed as zero.

### agentic

```json
{
  "executions": 1,
  "completion_rate": 0.0,
  "median_latency_ms": 14432.5,
  "p95_latency_ms": 14432.5,
  "median_reported_tokens": null,
  "token_observations": 0,
  "mean_model_calls": 10,
  "retry_execution_rate": 1.0,
  "validation_failure_execution_rate": 0.0,
  "validation_failure_per_check_rate": null,
  "known_cost_subtotal_usd": null,
  "unknown_cost_executions": 1,
  "not_applicable_cost_executions": 0,
  "total_estimated_cost_usd": null,
  "provider_429_events": 1,
  "provider_5xx_events": 0,
  "other_provider_failures": 0,
  "controller_output_failures": 2,
  "provider_successful_attempts": 9,
  "provider_failed_attempts": 1,
  "accepted_output_attempts": 4,
  "rejected_output_attempts": 2,
  "unassessed_output_attempts": 3,
  "pacing_wait_ms": 0.0,
  "provider_execution_ms": 11931.75,
  "inter_execution_wait_ms": 0.0
}
```

## Human factual review

Factual quality: not_evaluated. Generated answer keys and valid references are not factual proof.

```json
{
  "status": "not_evaluated"
}
```

## Failure examples

- recall-water-cycle / agentic: provider_rate_limit — Execution failed; see safe error category and trace.

## Terminal attribution

- 9875f77dd4ed4db79b5b2c7aae419941: compatibility code=unavailable; underlying=provider_rate_limit; guard=decision_failure_limit

## Limitations

Five synthetic cases are a convenience sample, not independent coverage of real curricula. Repetitions share sources. No significance or superiority claim is supported. Offline scripted runs measure artifact plumbing only. Cold imports, graph compilation, provider load, aliases/revisions, sampling defaults and order remain confounders. Alternating order reduces time-order bias but cannot remove it. The same generation model, settings, attempt limits, source documents and retrieval implementation are used; agent-selected queries/evidence and revision context can differ. Equal total token ceilings do not imply equal call counts. Token reservations use conservative bytes plus output ceilings, not measured tokenization. Deadlines are cooperative. Failed drafts are not retained; structural diagnostics describe accepted quizzes. Unknown pricing and incomplete usage stay unknown. Human results describe reviewed questions only and may have selection/reviewer bias.
