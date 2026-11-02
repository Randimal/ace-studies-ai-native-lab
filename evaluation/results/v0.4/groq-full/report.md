# Controlled architecture benchmark

Mode: full; transport: live. Completed 30/30 executions.

## Measurements

P95 uses nearest rank. With 1–15 observations per architecture it is unstable and often the maximum. Token medians include only complete reported usage. Latencies include failures.

### deterministic

```json
{
  "executions": 15,
  "completion_rate": 0.4,
  "median_latency_ms": 2376.19,
  "p95_latency_ms": 6508.53,
  "median_reported_tokens": 1375,
  "token_observations": 3,
  "mean_model_calls": 2.533333333333333,
  "retry_execution_rate": 0.8,
  "validation_failure_execution_rate": 0.06666666666666667,
  "validation_failure_per_check_rate": 0.14285714285714285,
  "known_cost_subtotal_usd": null,
  "unknown_cost_executions": 15,
  "not_applicable_cost_executions": 0,
  "total_estimated_cost_usd": null
}
```

### agentic

```json
{
  "executions": 15,
  "completion_rate": 0.0,
  "median_latency_ms": 2391.29,
  "p95_latency_ms": 12283.57,
  "median_reported_tokens": null,
  "token_observations": 0,
  "mean_model_calls": 4.066666666666666,
  "retry_execution_rate": 0.06666666666666667,
  "validation_failure_execution_rate": 0.0,
  "validation_failure_per_check_rate": null,
  "known_cost_subtotal_usd": null,
  "unknown_cost_executions": 15,
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

- recall-water-cycle / agentic: invalid_decision — Execution failed; see safe error category and trace.
- recall-water-cycle / agentic: invalid_decision — Execution failed; see safe error category and trace.
- recall-water-cycle / deterministic: unavailable — Execution failed; see safe error category and trace.
- recall-water-cycle / deterministic: unavailable — Execution failed; see safe error category and trace.
- recall-water-cycle / agentic: invalid_decision — Execution failed; see safe error category and trace.
- concept-retrieval-practice / agentic: invalid_decision — Execution failed; see safe error category and trace.
- concept-retrieval-practice / deterministic: unavailable — Execution failed; see safe error category and trace.
- concept-retrieval-practice / agentic: invalid_decision — Execution failed; see safe error category and trace.
- concept-retrieval-practice / agentic: invalid_decision — Execution failed; see safe error category and trace.
- concept-retrieval-practice / deterministic: unavailable — Execution failed; see safe error category and trace.
- reasoning-water-budget / agentic: invalid_decision — Execution failed; see safe error category and trace.
- reasoning-water-budget / agentic: invalid_decision — Execution failed; see safe error category and trace.
- reasoning-water-budget / deterministic: unavailable — Execution failed; see safe error category and trace.
- reasoning-water-budget / agentic: invalid_decision — Execution failed; see safe error category and trace.
- insufficient-factory-output / agentic: invalid_decision — Execution failed; see safe error category and trace.
- insufficient-factory-output / deterministic: unavailable — Execution failed; see safe error category and trace.
- insufficient-factory-output / agentic: invalid_decision — Execution failed; see safe error category and trace.
- insufficient-factory-output / agentic: invalid_decision — Execution failed; see safe error category and trace.
- ambiguous-lake-temperature / deterministic: unavailable — Execution failed; see safe error category and trace.
- ambiguous-lake-temperature / agentic: invalid_decision — Execution failed; see safe error category and trace.
- ambiguous-lake-temperature / agentic: invalid_decision — Execution failed; see safe error category and trace.
- ambiguous-lake-temperature / deterministic: unavailable — Execution failed; see safe error category and trace.
- ambiguous-lake-temperature / deterministic: unavailable — Execution failed; see safe error category and trace.
- ambiguous-lake-temperature / agentic: invalid_decision — Execution failed; see safe error category and trace.

## Limitations

Five synthetic cases are a convenience sample, not independent coverage of real curricula. Repetitions share sources. No significance or superiority claim is supported. Offline scripted runs measure artifact plumbing only. Cold imports, graph compilation, provider load, aliases/revisions, sampling defaults and order remain confounders. Alternating order reduces time-order bias but cannot remove it. The same generation model, settings, attempt limits, source documents and retrieval implementation are used; agent-selected queries/evidence and revision context can differ. Equal total token ceilings do not imply equal call counts. Token reservations use conservative bytes plus output ceilings, not measured tokenization. Deadlines are cooperative. Failed drafts are not retained; structural diagnostics describe accepted quizzes. Unknown pricing and incomplete usage stay unknown. Human results describe reviewed questions only and may have selection/reviewer bias.
