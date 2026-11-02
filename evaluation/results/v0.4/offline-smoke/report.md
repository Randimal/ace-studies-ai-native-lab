# Controlled architecture benchmark

Mode: smoke; transport: scripted-offline-not-a-model. Completed 2/2 executions.

## Measurements

P95 uses nearest rank. With 1–15 observations per architecture it is unstable and often the maximum. Token medians include only complete reported usage. Latencies include failures.

### deterministic

```json
{
  "executions": 1,
  "completion_rate": 1.0,
  "median_latency_ms": 5.04,
  "p95_latency_ms": 5.04,
  "median_reported_tokens": null,
  "token_observations": 0,
  "mean_model_calls": 1,
  "retry_execution_rate": 0.0,
  "validation_failure_execution_rate": 0.0,
  "validation_failure_per_check_rate": 0.0,
  "known_cost_subtotal_usd": null,
  "unknown_cost_executions": 1,
  "not_applicable_cost_executions": 0,
  "total_estimated_cost_usd": null
}
```

### agentic

```json
{
  "executions": 1,
  "completion_rate": 1.0,
  "median_latency_ms": 5558.82,
  "p95_latency_ms": 5558.82,
  "median_reported_tokens": null,
  "token_observations": 0,
  "mean_model_calls": 5,
  "retry_execution_rate": 0.0,
  "validation_failure_execution_rate": 0.0,
  "validation_failure_per_check_rate": 0.0,
  "known_cost_subtotal_usd": null,
  "unknown_cost_executions": 1,
  "not_applicable_cost_executions": 0,
  "total_estimated_cost_usd": null
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


## Limitations

Five synthetic cases are a convenience sample, not independent coverage of real curricula. Repetitions share sources. No significance or superiority claim is supported. Offline scripted runs measure artifact plumbing only. Cold imports, graph compilation, provider load, aliases/revisions, sampling defaults and order remain confounders. Alternating order reduces time-order bias but cannot remove it. The same generation model, settings, attempt limits, source documents and retrieval implementation are used; agent-selected queries/evidence and revision context can differ. Equal total token ceilings do not imply equal call counts. Token reservations use conservative bytes plus output ceilings, not measured tokenization. Deadlines are cooperative. Failed drafts are not retained; structural diagnostics describe accepted quizzes. Unknown pricing and incomplete usage stay unknown. Human results describe reviewed questions only and may have selection/reviewer bias.
