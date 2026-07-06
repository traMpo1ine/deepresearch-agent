# Formal Verifier Benchmark

## Protocol

- dataset: `synthetic_balanced_verifier`
- repetitions: `3`
- case_count_per_repetition: `120`
- judge: `deepseek`
- model: `deepseek-v4-flash`
- run_real: `true`
- boundary: Formal verifier benchmark for claim/evidence classification; not an end-to-end DeepResearch benchmark and not a production factuality guarantee.

## Summary

- total_cases: `360`
- total_attempted: `360`
- accuracy: `0.842`
- accuracy_mean: `0.842`
- accuracy_std: `0.000`
- heuristic_accuracy_mean: `0.467`
- macro_precision: `0.857`
- macro_recall: `0.842`
- macro_f1: `0.831`
- total_tokens: `63211`
- estimated_cost_rmb: `0.05893803`
- latency_seconds_mean: `143.310`

## Per-Class Metrics

| class | support | predicted | precision | recall | f1 |
| --- | ---:| ---:| ---:| ---:| ---:|
| supported | 90 | 87 | 0.966 | 0.933 | 0.949 |
| partial | 90 | 51 | 0.882 | 0.500 | 0.638 |
| unsupported | 90 | 119 | 0.714 | 0.944 | 0.813 |
| contradicted | 90 | 103 | 0.864 | 0.989 | 0.922 |

## Confusion Matrix

| expected \ predicted | supported | partial | unsupported | contradicted | skipped |
| --- | ---:| ---:| ---:| ---:| ---:|
| supported | 84 | 6 | 0 | 0 | 0 |
| partial | 3 | 45 | 33 | 9 | 0 |
| unsupported | 0 | 0 | 85 | 5 | 0 |
| contradicted | 0 | 0 | 1 | 89 | 0 |

## Repetitions

- run 1: accuracy=0.8416666666666667, errors=19, tokens=21100, cost_rmb=0.01970623, latency=143.572s
- run 2: accuracy=0.8416666666666667, errors=19, tokens=21074, cost_rmb=0.01965345, latency=144.803s
- run 3: accuracy=0.8416666666666667, errors=19, tokens=21037, cost_rmb=0.01957835, latency=141.556s

## Error Cases

- run `1` `lve_002_p` expected=partial heuristic=partial llm=unsupported: SQLite stores run traces and also guarantees distributed multi-node scheduling.
- run `1` `lve_003_p` expected=partial heuristic=partial llm=unsupported: The numpy vector index performs similarity recall and uses a production FAISS cluster by default.
- run `1` `lve_004_p` expected=partial heuristic=partial llm=unsupported: TextRank compression preserves citation quotes and guarantees that no relevant context is ever lost.
- run `1` `lve_006_p` expected=partial heuristic=partial llm=unsupported: Blue repair actions include ADD, DELETE, MODIFY, VERIFY, and automatic database migration.
- run `1` `lve_008_s` expected=supported heuristic=supported llm=partial: StructuredOutputParser supports strict JSON, extraction fallback, and schema-default repair.
- run `1` `lve_008_p` expected=partial heuristic=partial llm=unsupported: StructuredOutputParser repairs common JSON issues and guarantees semantic factual correctness.
- run `1` `lve_009_p` expected=partial heuristic=partial llm=unsupported: Claim Preflight flags overstrong assertions and replaces the full verifier in all benchmarks.
- run `1` `lve_010_p` expected=partial heuristic=unsupported llm=unsupported: The Web Demo shows trace views and implements production multi-user authentication.
- run `1` `lve_012_p` expected=partial heuristic=partial llm=supported: DeepSeek provider smoke is dry-run by default and contributes to offline benchmark scores.
- run `1` `lve_014_p` expected=partial heuristic=partial llm=unsupported: Offline benchmark metrics are reproducible and therefore prove production generalization.
- run `1` `lve_016_p` expected=partial heuristic=partial llm=unsupported: The extended ablation run compares several profiles and includes production user traffic.
- run `1` `lve_017_p` expected=partial heuristic=partial llm=unsupported: Bootstrap confidence intervals report uncertainty and prove the system is unbiased.
- run `1` `lve_018_p` expected=partial heuristic=partial llm=contradicted: Cohen's d reports effect size and replaces all other benchmark metrics.
- run `1` `lve_018_u` expected=unsupported heuristic=partial llm=contradicted: Cohen's d configures the DeepSeek base URL.
- run `1` `lve_019_c` expected=contradicted heuristic=supported llm=unsupported: Local corpus profiles require live open-web search for every run.
- run `1` `lve_022_p` expected=partial heuristic=partial llm=contradicted: The task state machine records lifecycle states and guarantees no task can fail.
- run `1` `lve_025_s` expected=supported heuristic=supported llm=partial: build_showcase writes report, trace, verifier, redblue, and backend artifact files.
- run `1` `lve_027_p` expected=partial heuristic=partial llm=unsupported: Experiment reports include failure cases and automatically prove every future run will pass.
- run `1` `lve_030_p` expected=partial heuristic=partial llm=contradicted: The current system is a local portfolio demo and already supports enterprise billing.
- run `2` `lve_029_p` expected=partial heuristic=partial llm=unsupported: Real provider calls read environment variables and automatically rotate keys across accounts.
- run `2` `lve_030_u` expected=unsupported heuristic=partial llm=contradicted: The portfolio boundary determines vector cosine similarity.