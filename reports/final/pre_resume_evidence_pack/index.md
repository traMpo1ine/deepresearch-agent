# DeepResearch Agent Pre-Resume Evidence Pack

Generated at: `2026-07-06T14:03:35`

This pack freezes the evidence needed before drafting the final resume entry.

## Key Artifacts

- `extended_researchbench_summary.md`: 60-case extended ablation summary.
- `extended_researchbench_metrics.json`: machine-readable extended ablation metrics.
- `formal_verifier_benchmark.md`: 3-run DeepSeek verifier benchmark report.
- `formal_verifier_benchmark.json`: machine-readable verifier benchmark aggregate.
- `assets/web_demo_showcase.png`: Web Demo screenshot.

## Extended ResearchBench Ablation

- run id: `20260705_020934_092414_researchbench_263e905e`
- profiles: `['baseline', 'full', 'redblue', 'verifier']`
- baseline judge: `0.764`
- full judge: `0.880`
- judge delta full-baseline: `0.115`
- baseline weak support: `1.000`
- full weak support: `0.431`
- weak support delta full-baseline: `-0.569`
- full repair precision: `0.944`
- full repair coverage: `1.000`

## Formal Verifier Benchmark

- dataset: `synthetic_balanced_verifier`
- model: `deepseek-v4-flash`
- repetitions: `3`
- total cases: `360`
- DeepSeek accuracy: `0.842`
- heuristic accuracy mean: `0.467`
- macro precision: `0.857`
- macro recall: `0.842`
- macro F1: `0.831`
- estimated cost RMB: `0.05893803`

## Boundaries

- Extended ResearchBench metrics are offline/mock pipeline metrics.
- Formal verifier benchmark is claim/evidence classification, not end-to-end DeepResearch quality.
- DeepSeek provider outputs are real API calls but remain separate from offline/mock benchmark metrics.
- The Web Demo is a local portfolio app, not a production multi-user SaaS.

## Manifest

See `manifest.json` for structured paths, dataset summaries, and headline metrics.
