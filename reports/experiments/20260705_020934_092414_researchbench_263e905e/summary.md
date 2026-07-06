# DeepResearch Agent Experiment Summary

Dataset: `data\benchmarks\researchbench_extended.jsonl`
Suite: `researchbench`
Cases: `60`
Payload validation: `passed`

| experiment | judge | 95% CI | hallucination | weak support | citation | atomic support | repair precision | repair coverage | convergence | oscillation | rounds | Cohen's d |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.764 | [0.752, 0.777] | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 7.273 |
| verifier | 0.872 | [0.853, 0.892] | 0.061 | 0.522 | 1.000 | 0.624 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.641 |
| redblue | 0.881 | [0.861, 0.903] | 0.000 | 0.425 | 1.000 | 0.677 | 0.953 | 1.000 | 1.000 | 0.533 | 2.000 | 1.736 |
| full | 0.880 | [0.860, 0.900] | 0.000 | 0.431 | 1.000 | 0.677 | 0.944 | 1.000 | 1.000 | 0.550 | 2.000 | 1.709 |

## Judge Dimensions

- `baseline`: factuality=0.000, coverage=0.872, citation_quality=1.000, structure=1.000, usefulness=0.949
- `verifier`: factuality=0.539, coverage=0.872, citation_quality=1.000, structure=1.000, usefulness=0.949
- `redblue`: factuality=0.575, coverage=0.878, citation_quality=1.000, structure=1.000, usefulness=0.951
- `full`: factuality=0.569, coverage=0.878, citation_quality=1.000, structure=1.000, usefulness=0.951

## Failure Cases

### baseline
- `rbx_001`: 3 claims require stronger support.
- `rbx_002`: 3 claims require stronger support.
- `rbx_003`: 3 claims require stronger support.
- `rbx_004`: 3 claims require stronger support.
- `rbx_005`: 3 claims require stronger support.

### verifier
- `rbx_001`: 2 claims require stronger support.
- `rbx_002`: 2 claims require stronger support.
- `rbx_003`: 2 claims require stronger support.
- `rbx_004`: 2 claims require stronger support.
- `rbx_005`: 1 claims require stronger support.

### redblue
- `rbx_001`: 1 claims require stronger support.
- `rbx_002`: 2 claims require stronger support.
- `rbx_003`: 1 claims require stronger support.
- `rbx_004`: 2 claims require stronger support.
- `rbx_005`: 1 claims require stronger support.

### full
- `rbx_001`: 2 claims require stronger support.
- `rbx_002`: 2 claims require stronger support.
- `rbx_004`: 2 claims require stronger support.
- `rbx_005`: 1 claims require stronger support.
- `rbx_006`: 2 claims require stronger support.


## Per-Category Metrics

### baseline
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 12 | 0.761 | 0.000 | 1.000 | 1.000 |
| multi_hop_reasoning | 12 | 0.792 | 0.000 | 1.000 | 1.000 |
| risk_analysis | 12 | 0.738 | 0.000 | 1.000 | 1.000 |
| technical_comparison | 12 | 0.792 | 0.000 | 1.000 | 1.000 |
| solution_design | 12 | 0.738 | 0.000 | 1.000 | 1.000 |

### verifier
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 12 | 0.844 | 0.167 | 0.750 | 1.000 |
| multi_hop_reasoning | 12 | 0.879 | 0.083 | 0.611 | 1.000 |
| risk_analysis | 12 | 0.834 | 0.028 | 0.583 | 1.000 |
| technical_comparison | 12 | 0.977 | 0.000 | 0.000 | 1.000 |
| solution_design | 12 | 0.826 | 0.028 | 0.667 | 1.000 |

### redblue
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 12 | 0.858 | 0.000 | 0.514 | 1.000 |
| multi_hop_reasoning | 12 | 0.890 | 0.000 | 0.472 | 1.000 |
| risk_analysis | 12 | 0.843 | 0.000 | 0.514 | 1.000 |
| technical_comparison | 12 | 0.984 | 0.000 | 0.000 | 1.000 |
| solution_design | 12 | 0.828 | 0.000 | 0.625 | 1.000 |

### full
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 12 | 0.858 | 0.000 | 0.514 | 1.000 |
| multi_hop_reasoning | 12 | 0.890 | 0.000 | 0.472 | 1.000 |
| risk_analysis | 12 | 0.837 | 0.000 | 0.542 | 1.000 |
| technical_comparison | 12 | 0.984 | 0.000 | 0.000 | 1.000 |
| solution_design | 12 | 0.828 | 0.000 | 0.625 | 1.000 |


## Per-Domain Metrics

### baseline
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 11 | 0.766 | 0.000 | 1.000 | 0.000 |
| memory_retrieval | 2 | 0.800 | 0.000 | 1.000 | 0.000 |
| context_compression | 4 | 0.777 | 0.000 | 1.000 | 0.000 |
| llm_backend | 6 | 0.753 | 0.000 | 1.000 | 0.000 |
| rag_system | 8 | 0.800 | 0.000 | 1.000 | 0.000 |
| evaluation | 7 | 0.747 | 0.000 | 1.000 | 0.000 |
| redblue_repair | 5 | 0.725 | 0.000 | 1.000 | 0.000 |
| agent_orchestration | 4 | 0.753 | 0.000 | 1.000 | 0.000 |
| engineering_tradeoff | 11 | 0.758 | 0.000 | 1.000 | 0.000 |
| reliability | 2 | 0.800 | 0.000 | 1.000 | 0.000 |

### verifier
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 11 | 0.875 | 0.000 | 0.455 | 0.000 |
| memory_retrieval | 2 | 0.933 | 0.000 | 0.333 | 0.000 |
| context_compression | 4 | 0.910 | 0.083 | 0.417 | 0.000 |
| llm_backend | 6 | 0.869 | 0.056 | 0.556 | 0.000 |
| rag_system | 8 | 0.892 | 0.042 | 0.583 | 0.000 |
| evaluation | 7 | 0.870 | 0.095 | 0.476 | 0.000 |
| redblue_repair | 5 | 0.827 | 0.067 | 0.467 | 0.000 |
| agent_orchestration | 4 | 0.830 | 0.167 | 0.667 | 0.000 |
| engineering_tradeoff | 11 | 0.863 | 0.091 | 0.606 | 0.000 |
| reliability | 2 | 0.900 | 0.000 | 0.500 | 0.000 |

### redblue
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 11 | 0.881 | 0.000 | 0.424 | 1.000 |
| memory_retrieval | 2 | 0.933 | 0.000 | 0.333 | 1.000 |
| context_compression | 4 | 0.910 | 0.000 | 0.333 | 1.000 |
| llm_backend | 6 | 0.874 | 0.000 | 0.472 | 0.944 |
| rag_system | 8 | 0.904 | 0.000 | 0.479 | 0.958 |
| evaluation | 7 | 0.880 | 0.000 | 0.333 | 0.905 |
| redblue_repair | 5 | 0.859 | 0.000 | 0.333 | 0.900 |
| agent_orchestration | 4 | 0.830 | 0.000 | 0.500 | 1.000 |
| engineering_tradeoff | 11 | 0.872 | 0.000 | 0.470 | 0.909 |
| reliability | 2 | 0.900 | 0.000 | 0.500 | 1.000 |

### full
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 11 | 0.875 | 0.000 | 0.455 | 1.000 |
| memory_retrieval | 2 | 0.933 | 0.000 | 0.333 | 1.000 |
| context_compression | 4 | 0.927 | 0.000 | 0.250 | 0.875 |
| llm_backend | 6 | 0.874 | 0.000 | 0.472 | 0.944 |
| rag_system | 8 | 0.896 | 0.000 | 0.521 | 0.958 |
| evaluation | 7 | 0.880 | 0.000 | 0.333 | 0.905 |
| redblue_repair | 5 | 0.859 | 0.000 | 0.333 | 0.900 |
| agent_orchestration | 4 | 0.830 | 0.000 | 0.500 | 1.000 |
| engineering_tradeoff | 11 | 0.872 | 0.000 | 0.470 | 0.909 |
| reliability | 2 | 0.900 | 0.000 | 0.500 | 1.000 |


## Multi-Hop And Hotpot Subsets

- `baseline` multi-hop: n=12, judge=0.792, repair_precision=0.000
- `baseline` hotpot-style: n=12, judge=0.792, repair_precision=0.000
- `verifier` multi-hop: n=12, judge=0.879, repair_precision=0.000
- `verifier` hotpot-style: n=12, judge=0.879, repair_precision=0.000
- `redblue` multi-hop: n=12, judge=0.890, repair_precision=0.903
- `redblue` hotpot-style: n=12, judge=0.890, repair_precision=0.903
- `full` multi-hop: n=12, judge=0.890, repair_precision=0.903
- `full` hotpot-style: n=12, judge=0.890, repair_precision=0.903

## Repair Action Distribution

- `baseline`: none
- `verifier`: none
- `redblue`: add=32, delete=8, modify=73
- `full`: add=33, delete=9, modify=74

## Integrity Report

- Dataset summary: `{'path': 'data\\benchmarks\\researchbench_extended.jsonl', 'case_count': 60, 'answer_type_counts': {'factual_explanation': 12, 'multi_hop_reasoning': 12, 'risk_analysis': 12, 'technical_comparison': 12, 'solution_design': 12}, 'domain_counts': {'citation_verification': 11, 'memory_retrieval': 2, 'context_compression': 4, 'llm_backend': 6, 'rag_system': 8, 'evaluation': 7, 'redblue_repair': 5, 'agent_orchestration': 4, 'engineering_tradeoff': 11, 'reliability': 2}, 'difficulty_counts': {'easy': 13, 'medium': 42, 'hard': 5}, 'suite_source_counts': {'researchbench': 60}, 'average_required_hops': 1.2, 'multi_hop_count': 12, 'hotpot_style_count': 12}`
- Suite source counts: `{'researchbench': 60}`
- Experiment artifacts: `{'baseline': {'memory_path': 'data\\memory\\deepresearch_baseline.sqlite3', 'vector_path': 'data\\memory\\vector_index_baseline.npz', 'plan_dir': 'reports\\plans\\baseline'}, 'verifier': {'memory_path': 'data\\memory\\deepresearch_verifier.sqlite3', 'vector_path': 'data\\memory\\vector_index_verifier.npz', 'plan_dir': 'reports\\plans\\verifier'}, 'redblue': {'memory_path': 'data\\memory\\deepresearch_redblue.sqlite3', 'vector_path': 'data\\memory\\vector_index_redblue.npz', 'plan_dir': 'reports\\plans\\redblue'}, 'full': {'memory_path': 'data\\memory\\deepresearch_full.sqlite3', 'vector_path': 'data\\memory\\vector_index_full.npz', 'plan_dir': 'reports\\plans\\full'}}`