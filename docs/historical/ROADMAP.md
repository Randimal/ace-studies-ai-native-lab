# AI-Native Engineering roadmap

- **v0.4 — Current: Controlled Architecture Benchmarking and Reporting.** Extends the existing runner with paired smoke and alternating 30-execution Groq pilot schedules, common generation settings/budgets, sanitized configuration, atomic checkpoints/resume, JSON/CSV/Markdown outputs, and blind consensus human review. Live calls require explicit CLI opt-in. Jev remains optional outside the default experiment. See [BENCHMARK.md](BENCHMARK.md) for all five command sequences and the rubric. Implementation/tests make no live calls; live pilot evidence and human factual assessment remain future research work. Five synthetic cases and single live observations do not support generalizable conclusions.

- v0.1 — Deterministic sentence baseline and multi-provider abstraction.
- v0.2 — PDF/notes processing, deterministic chunks, lexical retrieval, citations and structural evaluation.
- v0.2.1 — MCQ quality checks, student-safe attempts, and a versioned synthetic dataset/JSON evaluation runner.
- v0.3 — one genuinely model-directed LangGraph controller over the same services, typed constrained decisions, bounded execution, redacted traces, workflow selection and paired benchmark reports. The deterministic architecture remains the default comparison baseline.
- v0.3.1 — Optional TypeSafe Jev Choice controller, configured-provider quiz generation, explicit uncertainty policy, separate usage/cost metrics and three-way benchmarks. No hidden fallback; live TypeSafe verification pending.
- Next — Controlled Part 2 trials with pinned model revisions, repeated samples/order control, explicit matched budgets, and human review of factual correctness, ambiguity and pedagogical quality. No claim that autonomy improves results without measurements.
- Later — Broader datasets, OWASP-aligned research, least-privilege external tool experiments, policy gates and operational patterns, each evaluated separately.

No cooperating agents, long-term memory, database, distributed workers, public deployment stack or external autonomous actions are implemented. Structural/citation success and student scores are not independent factual-grounding evaluation.
