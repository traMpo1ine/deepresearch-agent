# DeepResearch Agent Experiment Summary

Dataset: `data\benchmarks\adversarial_researchbench.jsonl`
Suite: `adversarial`
Cases: `10`
Payload validation: `passed`

| experiment | judge | 95% CI | hallucination | weak support | citation | atomic support | repair precision | repair coverage | convergence | oscillation | rounds | Cohen's d |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.791 | [0.772, 0.800] | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 14.681 |
| verifier | 0.907 | [0.880, 0.933] | 0.100 | 0.567 | 1.000 | 0.629 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 3.134 |
| redblue | 0.920 | [0.893, 0.950] | 0.000 | 0.400 | 1.000 | 0.764 | 0.883 | 1.000 | 1.000 | 0.500 | 2.000 | 3.312 |

## Judge Dimensions

- `baseline`: factuality=0.000, coverage=0.967, citation_quality=1.000, structure=1.000, usefulness=0.987
- `verifier`: factuality=0.533, coverage=1.000, citation_quality=1.000, structure=1.000, usefulness=1.000
- `redblue`: factuality=0.600, coverage=1.000, citation_quality=1.000, structure=1.000, usefulness=1.000

## Failure Cases

### baseline
- `arb_001`: Report contains prohibited claim cue: guarantees perfect factuality; 3 claims require stronger support.
- `arb_002`: 3 claims require stronger support.
- `arb_003`: 3 claims require stronger support.
- `arb_004`: Report contains prohibited claim cue: delete every partial claim; 3 claims require stronger support.
- `arb_005`: Report contains prohibited claim cue: absolute ground truth; 3 claims require stronger support.

### verifier
- `arb_001`: Report contains prohibited claim cue: guarantees perfect factuality; 1 claims require stronger support.
- `arb_002`: 1 claims require stronger support.
- `arb_003`: 2 claims require stronger support.
- `arb_004`: Report contains prohibited claim cue: delete every partial claim; 2 claims require stronger support.
- `arb_005`: Report contains prohibited claim cue: absolute ground truth; 3 claims require stronger support.

### redblue
- `arb_001`: Report contains prohibited claim cue: guarantees perfect factuality; 1 claims require stronger support.
- `arb_002`: 1 claims require stronger support.
- `arb_003`: 2 claims require stronger support.
- `arb_004`: Report contains prohibited claim cue: delete every partial claim
- `arb_005`: Report contains prohibited claim cue: absolute ground truth; 1 claims require stronger support.


## Per-Category Metrics

### baseline
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| risk_analysis | 5 | 0.781 | 0.000 | 1.000 | 1.000 |
| factual_explanation | 1 | 0.800 | 0.000 | 1.000 | 1.000 |
| technical_comparison | 3 | 0.800 | 0.000 | 1.000 | 1.000 |
| solution_design | 1 | 0.800 | 0.000 | 1.000 | 1.000 |

### verifier
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| risk_analysis | 5 | 0.893 | 0.067 | 0.600 | 1.000 |
| factual_explanation | 1 | 0.933 | 0.000 | 0.333 | 1.000 |
| technical_comparison | 3 | 0.933 | 0.222 | 0.556 | 1.000 |
| solution_design | 1 | 0.867 | 0.000 | 0.667 | 1.000 |

### redblue
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| risk_analysis | 5 | 0.900 | 0.000 | 0.500 | 1.000 |
| factual_explanation | 1 | 0.933 | 0.000 | 0.333 | 1.000 |
| technical_comparison | 3 | 0.967 | 0.000 | 0.167 | 1.000 |
| solution_design | 1 | 0.867 | 0.000 | 0.667 | 1.000 |


## Per-Domain Metrics

### baseline
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| context_compression | 1 | 0.707 | 0.000 | 1.000 | 0.000 |
| redblue_repair | 1 | 0.800 | 0.000 | 1.000 | 0.000 |
| engineering_tradeoff | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| memory_retrieval | 2 | 0.800 | 0.000 | 1.000 | 0.000 |

### verifier
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.956 | 0.000 | 0.222 | 0.000 |
| context_compression | 1 | 0.867 | 0.000 | 0.667 | 0.000 |
| redblue_repair | 1 | 0.933 | 0.333 | 0.667 | 0.000 |
| engineering_tradeoff | 3 | 0.889 | 0.111 | 0.667 | 0.000 |
| memory_retrieval | 2 | 0.867 | 0.167 | 0.833 | 0.000 |

### redblue
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.956 | 0.000 | 0.222 | 1.000 |
| context_compression | 1 | 0.867 | 0.000 | 0.667 | 1.000 |
| redblue_repair | 1 | 1.000 | 0.000 | 0.000 | 0.500 |
| engineering_tradeoff | 3 | 0.900 | 0.000 | 0.500 | 0.889 |
| memory_retrieval | 2 | 0.883 | 0.000 | 0.583 | 0.833 |


## Multi-Hop And Hotpot Subsets

- `baseline` multi-hop: n=7, judge=0.787, repair_precision=0.000
- `baseline` hotpot-style: n=0, judge=0.000, repair_precision=0.000
- `verifier` multi-hop: n=7, judge=0.895, repair_precision=0.000
- `verifier` hotpot-style: n=0, judge=0.000, repair_precision=0.000
- `redblue` multi-hop: n=7, judge=0.905, repair_precision=0.905
- `redblue` hotpot-style: n=0, judge=0.000, repair_precision=0.000

## Repair Action Distribution

- `baseline`: none
- `verifier`: none
- `redblue`: add=5, delete=3, modify=11

## Integrity Report

- Dataset summary: `{'path': 'data\\benchmarks\\adversarial_researchbench.jsonl', 'case_count': 10, 'answer_type_counts': {'risk_analysis': 5, 'factual_explanation': 1, 'technical_comparison': 3, 'solution_design': 1}, 'domain_counts': {'citation_verification': 3, 'context_compression': 1, 'redblue_repair': 1, 'engineering_tradeoff': 3, 'memory_retrieval': 2}, 'difficulty_counts': {'medium': 6, 'easy': 1, 'hard': 3}, 'suite_source_counts': {'adversarial': 10}, 'average_required_hops': 1.7, 'multi_hop_count': 7, 'hotpot_style_count': 0}`
- Suite source counts: `{'adversarial': 10}`
- Experiment artifacts: `{'baseline': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\adversarial_baseline.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\adversarial_vector_baseline.npz', 'plan_dir': 'reports\\plans\\baseline'}, 'verifier': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\adversarial_verifier.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\adversarial_vector_verifier.npz', 'plan_dir': 'reports\\plans\\verifier'}, 'redblue': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\adversarial_redblue.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\adversarial_vector_redblue.npz', 'plan_dir': 'reports\\plans\\redblue'}}`