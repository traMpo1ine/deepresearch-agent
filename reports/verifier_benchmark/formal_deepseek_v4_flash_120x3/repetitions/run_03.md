# LLM Verifier Smoke

This smoke test compares the existing heuristic verifier with an optional LLM second-layer judge on a balanced claim/evidence set.

## Summary

- cases: `120`
- backend: `deepseek`
- model: `deepseek-v4-flash`
- run_real: `true`
- env_configured: `true`
- heuristic_accuracy: `0.467`
- llm_attempted: `120`
- llm_accuracy: `0.8416666666666667`
- llm_error_count: `19`
- total_tokens: `21037`
- estimated_cost_rmb: `0.01957835`
- boundary: LLM verifier smoke is a provider/second-layer check and is not part of offline benchmark metrics.

## Status Distribution

- expected: `{'contradicted': 30, 'partial': 30, 'supported': 30, 'unsupported': 30}`
- heuristic: `{'contradicted': 3, 'partial': 56, 'supported': 58, 'unsupported': 3}`
- llm: `{'contradicted': 35, 'partial': 17, 'supported': 29, 'unsupported': 39}`

## Per Expected Status

| expected | n | attempted | correct | accuracy |
| --- | ---:| ---:| ---:| ---:|
| supported | 30 | 30 | 28 | 0.933 |
| partial | 30 | 30 | 15 | 0.500 |
| unsupported | 30 | 30 | 28 | 0.933 |
| contradicted | 30 | 30 | 30 | 1.000 |

## Confusion Matrix

| expected \ llm | supported | partial | unsupported | contradicted | skipped |
| --- | ---:| ---:| ---:| ---:| ---:|
| supported | 28 | 2 | 0 | 0 | 0 |
| partial | 1 | 15 | 11 | 3 | 0 |
| unsupported | 0 | 0 | 28 | 2 | 0 |
| contradicted | 0 | 0 | 0 | 30 | 0 |

## Error Cases

- `lve_002_p` expected=partial heuristic=partial llm=unsupported: SQLite stores run traces and also guarantees distributed multi-node scheduling.
- `lve_003_p` expected=partial heuristic=partial llm=unsupported: The numpy vector index performs similarity recall and uses a production FAISS cluster by default.
- `lve_004_p` expected=partial heuristic=partial llm=unsupported: TextRank compression preserves citation quotes and guarantees that no relevant context is ever lost.
- `lve_006_p` expected=partial heuristic=partial llm=unsupported: Blue repair actions include ADD, DELETE, MODIFY, VERIFY, and automatic database migration.
- `lve_008_s` expected=supported heuristic=supported llm=partial: StructuredOutputParser supports strict JSON, extraction fallback, and schema-default repair.
- `lve_008_p` expected=partial heuristic=partial llm=unsupported: StructuredOutputParser repairs common JSON issues and guarantees semantic factual correctness.
- `lve_009_p` expected=partial heuristic=partial llm=unsupported: Claim Preflight flags overstrong assertions and replaces the full verifier in all benchmarks.
- `lve_010_p` expected=partial heuristic=unsupported llm=unsupported: The Web Demo shows trace views and implements production multi-user authentication.
- `lve_012_p` expected=partial heuristic=partial llm=supported: DeepSeek provider smoke is dry-run by default and contributes to offline benchmark scores.
- `lve_014_p` expected=partial heuristic=partial llm=unsupported: Offline benchmark metrics are reproducible and therefore prove production generalization.
- `lve_016_p` expected=partial heuristic=partial llm=unsupported: The extended ablation run compares several profiles and includes production user traffic.
- `lve_017_p` expected=partial heuristic=partial llm=unsupported: Bootstrap confidence intervals report uncertainty and prove the system is unbiased.
- `lve_018_p` expected=partial heuristic=partial llm=contradicted: Cohen's d reports effect size and replaces all other benchmark metrics.
- `lve_018_u` expected=unsupported heuristic=partial llm=contradicted: Cohen's d configures the DeepSeek base URL.
- `lve_022_p` expected=partial heuristic=partial llm=contradicted: The task state machine records lifecycle states and guarantees no task can fail.
- `lve_025_s` expected=supported heuristic=supported llm=partial: build_showcase writes report, trace, verifier, redblue, and backend artifact files.
- `lve_027_p` expected=partial heuristic=partial llm=unsupported: Experiment reports include failure cases and automatically prove every future run will pass.
- `lve_030_p` expected=partial heuristic=partial llm=contradicted: The current system is a local portfolio demo and already supports enterprise billing.
- `lve_030_u` expected=unsupported heuristic=partial llm=contradicted: The portfolio boundary determines vector cosine similarity.

## Cases

| id | expected | heuristic | llm | cost_rmb |
| --- | --- | --- | --- | --- |
| lve_001_s | supported | supported | supported | 0.00021112 |
| lve_001_c | contradicted | supported | contradicted | 0.00021011 |
| lve_001_p | partial | contradicted | partial | 7.568e-05 |
| lve_001_u | unsupported | partial | unsupported | 0.00020402 |
| lve_002_s | supported | supported | supported | 0.00016804 |
| lve_002_c | contradicted | partial | contradicted | 0.00010207 |
| lve_002_p | partial | partial | unsupported | 7.771e-05 |
| lve_002_u | unsupported | partial | unsupported | 8.887e-05 |
| lve_003_s | supported | supported | supported | 0.00019691 |
| lve_003_c | contradicted | supported | contradicted | 0.00021214 |
| lve_003_p | partial | partial | unsupported | 0.00022533 |
| lve_003_u | unsupported | supported | unsupported | 0.00019285 |
| lve_004_s | supported | supported | supported | 0.00019996 |
| lve_004_c | contradicted | supported | contradicted | 0.00019996 |
| lve_004_p | partial | partial | unsupported | 0.00024157 |
| lve_004_u | unsupported | supported | unsupported | 0.00020097 |
| lve_005_s | supported | supported | supported | 0.00010004 |
| lve_005_c | contradicted | partial | contradicted | 0.00012034 |
| lve_005_p | partial | partial | partial | 0.00010917 |
| lve_005_u | unsupported | partial | unsupported | 0.00012135 |
| lve_006_s | supported | supported | supported | 8.887e-05 |
| lve_006_c | contradicted | supported | contradicted | 0.00014064 |
| lve_006_p | partial | partial | unsupported | 0.0001315 |
| lve_006_u | unsupported | partial | unsupported | 0.00012947 |
| lve_007_s | supported | supported | supported | 8.887e-05 |
| lve_007_c | contradicted | partial | contradicted | 0.00010613 |
| lve_007_p | partial | supported | partial | 0.00011831 |
| lve_007_u | unsupported | partial | unsupported | 0.00010004 |
| lve_008_s | supported | supported | partial | 0.00010714 |
| lve_008_c | contradicted | supported | contradicted | 0.00023751 |
| lve_008_p | partial | partial | unsupported | 0.00020909 |
| lve_008_u | unsupported | partial | unsupported | 0.00022229 |
| lve_009_s | supported | supported | supported | 0.00019996 |
| lve_009_c | contradicted | supported | contradicted | 0.00019387 |
| lve_009_p | partial | partial | unsupported | 0.00022634 |
| lve_009_u | unsupported | partial | unsupported | 0.00022229 |
| lve_010_s | supported | partial | supported | 0.00011425 |
| lve_010_c | contradicted | partial | contradicted | 0.00013556 |
| lve_010_p | partial | unsupported | unsupported | 0.00012034 |
| lve_010_u | unsupported | unsupported | unsupported | 0.0001244 |
| lve_011_s | supported | partial | supported | 8.583e-05 |
| lve_011_c | contradicted | supported | contradicted | 0.00014876 |
| lve_011_p | partial | partial | partial | 7.872e-05 |
| lve_011_u | unsupported | unsupported | unsupported | 8.684e-05 |
| lve_012_s | supported | partial | supported | 0.00014165 |
| lve_012_c | contradicted | supported | contradicted | 0.0001315 |
| lve_012_p | partial | partial | supported | 0.00016398 |
| lve_012_u | unsupported | partial | unsupported | 0.00010613 |
| lve_013_s | supported | supported | supported | 0.00012846 |
| lve_013_c | contradicted | supported | contradicted | 8.887e-05 |
| lve_013_p | partial | partial | partial | 0.00012643 |
| lve_013_u | unsupported | partial | unsupported | 9.902e-05 |
| lve_014_s | supported | supported | supported | 0.00018879 |
| lve_014_c | contradicted | supported | contradicted | 0.00020199 |
| lve_014_p | partial | partial | unsupported | 0.0002365 |
| lve_014_u | unsupported | supported | unsupported | 0.0002436 |
| lve_015_s | supported | supported | supported | 0.00011019 |
| lve_015_c | contradicted | supported | contradicted | 0.00010816 |
| lve_015_p | partial | partial | partial | 0.00011425 |
| lve_015_u | unsupported | partial | unsupported | 0.00011831 |
| lve_016_s | supported | supported | supported | 8.38e-05 |
| lve_016_c | contradicted | supported | contradicted | 0.00023751 |
| lve_016_p | partial | partial | unsupported | 7.974e-05 |
| lve_016_u | unsupported | partial | unsupported | 7.974e-05 |
| lve_017_s | supported | contradicted | supported | 0.00021518 |
| lve_017_c | contradicted | partial | contradicted | 0.0002436 |
| lve_017_p | partial | partial | unsupported | 0.00022533 |
| lve_017_u | unsupported | supported | unsupported | 0.00020909 |
| lve_018_s | supported | supported | supported | 0.00019285 |
| lve_018_c | contradicted | supported | contradicted | 0.00021721 |
| lve_018_p | partial | partial | contradicted | 0.00020605 |
| lve_018_u | unsupported | partial | contradicted | 0.00019488 |
| lve_019_s | supported | supported | supported | 0.0001041 |
| lve_019_c | contradicted | supported | contradicted | 8.786e-05 |
| lve_019_p | partial | partial | partial | 6.959e-05 |
| lve_019_u | unsupported | supported | unsupported | 0.00021112 |
| lve_020_s | supported | supported | supported | 0.00019488 |
| lve_020_c | contradicted | contradicted | contradicted | 0.00018879 |
| lve_020_p | partial | partial | partial | 0.00024157 |
| lve_020_u | unsupported | partial | unsupported | 0.00022533 |
| lve_021_s | supported | supported | supported | 0.00026492 |
| lve_021_c | contradicted | supported | contradicted | 0.00020503 |
| lve_021_p | partial | partial | partial | 0.00022431 |
| lve_021_u | unsupported | partial | unsupported | 0.00018981 |
| lve_022_s | supported | supported | supported | 8.887e-05 |
| lve_022_c | contradicted | supported | contradicted | 9.09e-05 |
| lve_022_p | partial | partial | contradicted | 9.598e-05 |
| lve_022_u | unsupported | supported | unsupported | 7.263e-05 |
| lve_023_s | supported | supported | supported | 0.00020199 |
| lve_023_c | contradicted | partial | contradicted | 0.00020808 |
| lve_023_p | partial | partial | partial | 0.00017357 |
| lve_023_u | unsupported | partial | unsupported | 0.00019996 |
| lve_024_s | supported | supported | supported | 0.00019691 |
| lve_024_c | contradicted | supported | contradicted | 0.00019894 |
| lve_024_p | partial | partial | partial | 0.00019996 |
| lve_024_u | unsupported | supported | unsupported | 0.00020706 |
| lve_025_s | supported | supported | partial | 0.00023605 |
| lve_025_c | contradicted | partial | contradicted | 0.00017007 |
| lve_025_p | partial | partial | partial | 0.0001518 |
| lve_025_u | unsupported | partial | unsupported | 9.902e-05 |
| lve_026_s | supported | supported | supported | 0.00023954 |
| lve_026_c | contradicted | supported | contradicted | 0.00020503 |
| lve_026_p | partial | partial | partial | 0.00024868 |
| lve_026_u | unsupported | supported | unsupported | 0.00018778 |
| lve_027_s | supported | supported | supported | 0.00016951 |
| lve_027_c | contradicted | supported | contradicted | 0.00016545 |
| lve_027_p | partial | partial | unsupported | 0.00020909 |
| lve_027_u | unsupported | supported | unsupported | 0.00016545 |
| lve_028_s | supported | supported | supported | 0.00013353 |
| lve_028_c | contradicted | supported | contradicted | 9.192e-05 |
| lve_028_p | partial | partial | partial | 0.00014267 |
| lve_028_u | unsupported | partial | unsupported | 9.293e-05 |
| lve_029_s | supported | supported | supported | 0.00018473 |
| lve_029_c | contradicted | supported | contradicted | 0.00023447 |
| lve_029_p | partial | partial | partial | 0.00019387 |
| lve_029_u | unsupported | partial | unsupported | 0.00021417 |
| lve_030_s | supported | supported | supported | 7.771e-05 |
| lve_030_c | contradicted | supported | contradicted | 0.00021619 |
| lve_030_p | partial | partial | contradicted | 0.00021417 |
| lve_030_u | unsupported | partial | contradicted | 0.00022432 |