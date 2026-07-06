# DeepResearch Agent Experiment Summary

Dataset: `data\benchmarks\researchbench.jsonl`
Suite: `researchbench`
Cases: `35`
Payload validation: `passed`

| experiment | judge | 95% CI | hallucination | weak support | citation | atomic support | repair precision | repair coverage | convergence | oscillation | rounds | Cohen's d |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.774 | [0.760, 0.787] | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 9.020 |
| memory | 0.779 | [0.764, 0.792] | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.129 |
| compression | 0.779 | [0.766, 0.791] | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.129 |
| verifier | 0.867 | [0.846, 0.887] | 0.095 | 0.657 | 1.000 | 0.471 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.760 |
| redblue | 0.880 | [0.859, 0.901] | 0.000 | 0.495 | 1.000 | 0.610 | 0.895 | 1.000 | 1.000 | 0.486 | 1.971 | 1.917 |
| full | 0.880 | [0.858, 0.903] | 0.000 | 0.495 | 1.000 | 0.610 | 0.895 | 1.000 | 1.000 | 0.486 | 1.971 | 1.917 |

## Judge Dimensions

- `baseline`: factuality=0.000, coverage=0.906, citation_quality=1.000, structure=1.000, usefulness=0.962
- `memory`: factuality=0.000, coverage=0.925, citation_quality=1.000, structure=1.000, usefulness=0.970
- `compression`: factuality=0.000, coverage=0.925, citation_quality=1.000, structure=1.000, usefulness=0.970
- `verifier`: factuality=0.438, coverage=0.925, citation_quality=1.000, structure=1.000, usefulness=0.970
- `redblue`: factuality=0.505, coverage=0.925, citation_quality=1.000, structure=1.000, usefulness=0.970
- `full`: factuality=0.505, coverage=0.925, citation_quality=1.000, structure=1.000, usefulness=0.970

## Failure Cases

### baseline
- `rb_001`: 3 claims require stronger support.
- `rb_002`: 3 claims require stronger support.
- `rb_003`: 3 claims require stronger support.
- `rb_004`: 3 claims require stronger support.
- `rb_005`: 3 claims require stronger support.

### memory
- `rb_001`: 3 claims require stronger support.
- `rb_002`: 3 claims require stronger support.
- `rb_003`: 3 claims require stronger support.
- `rb_004`: 3 claims require stronger support.
- `rb_005`: 3 claims require stronger support.

### compression
- `rb_001`: 3 claims require stronger support.
- `rb_002`: 3 claims require stronger support.
- `rb_003`: 3 claims require stronger support.
- `rb_004`: 3 claims require stronger support.
- `rb_005`: 3 claims require stronger support.

### verifier
- `rb_001`: 1 claims require stronger support.
- `rb_002`: 2 claims require stronger support.
- `rb_003`: 2 claims require stronger support.
- `rb_004`: 2 claims require stronger support.
- `rb_005`: 3 claims require stronger support.

### redblue
- `rb_001`: 1 claims require stronger support.
- `rb_002`: 2 claims require stronger support.
- `rb_003`: 2 claims require stronger support.
- `rb_004`: 2 claims require stronger support.
- `rb_005`: 1 claims require stronger support.

### full
- `rb_001`: 1 claims require stronger support.
- `rb_002`: 2 claims require stronger support.
- `rb_003`: 2 claims require stronger support.
- `rb_004`: 2 claims require stronger support.
- `rb_005`: 1 claims require stronger support.


## Per-Category Metrics

### baseline
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 29 | 0.776 | 0.000 | 1.000 | 1.000 |
| multi_hop_reasoning | 1 | 0.707 | 0.000 | 1.000 | 1.000 |
| risk_analysis | 2 | 0.800 | 0.000 | 1.000 | 1.000 |
| technical_comparison | 1 | 0.800 | 0.000 | 1.000 | 1.000 |
| solution_design | 2 | 0.730 | 0.000 | 1.000 | 1.000 |

### memory
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 29 | 0.783 | 0.000 | 1.000 | 1.000 |
| multi_hop_reasoning | 1 | 0.707 | 0.000 | 1.000 | 1.000 |
| risk_analysis | 2 | 0.800 | 0.000 | 1.000 | 1.000 |
| technical_comparison | 1 | 0.800 | 0.000 | 1.000 | 1.000 |
| solution_design | 2 | 0.730 | 0.000 | 1.000 | 1.000 |

### compression
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 29 | 0.783 | 0.000 | 1.000 | 1.000 |
| multi_hop_reasoning | 1 | 0.707 | 0.000 | 1.000 | 1.000 |
| risk_analysis | 2 | 0.800 | 0.000 | 1.000 | 1.000 |
| technical_comparison | 1 | 0.800 | 0.000 | 1.000 | 1.000 |
| solution_design | 2 | 0.730 | 0.000 | 1.000 | 1.000 |

### verifier
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 29 | 0.866 | 0.092 | 0.678 | 1.000 |
| multi_hop_reasoning | 1 | 0.773 | 0.667 | 1.333 | 1.000 |
| risk_analysis | 2 | 0.900 | 0.000 | 0.500 | 1.000 |
| technical_comparison | 1 | 1.000 | 0.000 | 0.000 | 1.000 |
| solution_design | 2 | 0.830 | 0.000 | 0.500 | 1.000 |

### redblue
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 29 | 0.877 | 0.000 | 0.529 | 1.000 |
| multi_hop_reasoning | 1 | 0.907 | 0.000 | 0.000 | 1.000 |
| risk_analysis | 2 | 0.900 | 0.000 | 0.500 | 1.000 |
| technical_comparison | 1 | 1.000 | 0.000 | 0.000 | 1.000 |
| solution_design | 2 | 0.830 | 0.000 | 0.500 | 1.000 |

### full
| category | n | judge | hallucination | weak support | citation |
|---|---:|---:|---:|---:|---:|
| factual_explanation | 29 | 0.877 | 0.000 | 0.529 | 1.000 |
| multi_hop_reasoning | 1 | 0.907 | 0.000 | 0.000 | 1.000 |
| risk_analysis | 2 | 0.900 | 0.000 | 0.500 | 1.000 |
| technical_comparison | 1 | 1.000 | 0.000 | 0.000 | 1.000 |
| solution_design | 2 | 0.830 | 0.000 | 0.500 | 1.000 |


## Per-Domain Metrics

### baseline
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| agent_orchestration | 5 | 0.735 | 0.000 | 1.000 | 0.000 |
| memory_retrieval | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| context_compression | 2 | 0.753 | 0.000 | 1.000 | 0.000 |
| redblue_repair | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| evaluation | 5 | 0.749 | 0.000 | 1.000 | 0.000 |
| multi_hop | 2 | 0.753 | 0.000 | 1.000 | 0.000 |
| llm_backend | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| engineering_tradeoff | 5 | 0.781 | 0.000 | 1.000 | 0.000 |
| reliability | 2 | 0.800 | 0.000 | 1.000 | 0.000 |
| rag_system | 2 | 0.772 | 0.000 | 1.000 | 0.000 |

### memory
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| agent_orchestration | 5 | 0.735 | 0.000 | 1.000 | 0.000 |
| memory_retrieval | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| context_compression | 2 | 0.753 | 0.000 | 1.000 | 0.000 |
| redblue_repair | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| evaluation | 5 | 0.767 | 0.000 | 1.000 | 0.000 |
| multi_hop | 2 | 0.753 | 0.000 | 1.000 | 0.000 |
| llm_backend | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| engineering_tradeoff | 5 | 0.800 | 0.000 | 1.000 | 0.000 |
| reliability | 2 | 0.800 | 0.000 | 1.000 | 0.000 |
| rag_system | 2 | 0.772 | 0.000 | 1.000 | 0.000 |

### compression
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| agent_orchestration | 5 | 0.735 | 0.000 | 1.000 | 0.000 |
| memory_retrieval | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| context_compression | 2 | 0.753 | 0.000 | 1.000 | 0.000 |
| redblue_repair | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| evaluation | 5 | 0.767 | 0.000 | 1.000 | 0.000 |
| multi_hop | 2 | 0.753 | 0.000 | 1.000 | 0.000 |
| llm_backend | 3 | 0.800 | 0.000 | 1.000 | 0.000 |
| engineering_tradeoff | 5 | 0.800 | 0.000 | 1.000 | 0.000 |
| reliability | 2 | 0.800 | 0.000 | 1.000 | 0.000 |
| rag_system | 2 | 0.772 | 0.000 | 1.000 | 0.000 |

### verifier
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.889 | 0.000 | 0.556 | 0.000 |
| agent_orchestration | 5 | 0.801 | 0.000 | 0.667 | 0.000 |
| memory_retrieval | 3 | 0.844 | 0.111 | 0.889 | 0.000 |
| context_compression | 2 | 0.820 | 0.000 | 0.667 | 0.000 |
| redblue_repair | 3 | 0.889 | 0.000 | 0.556 | 0.000 |
| evaluation | 5 | 0.874 | 0.200 | 0.667 | 0.000 |
| multi_hop | 2 | 0.887 | 0.333 | 0.667 | 0.000 |
| llm_backend | 3 | 0.867 | 0.111 | 0.778 | 0.000 |
| engineering_tradeoff | 5 | 0.907 | 0.200 | 0.667 | 0.000 |
| reliability | 2 | 0.900 | 0.000 | 0.500 | 0.000 |
| rag_system | 2 | 0.872 | 0.000 | 0.500 | 0.000 |

### redblue
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.889 | 0.000 | 0.556 | 1.000 |
| agent_orchestration | 5 | 0.801 | 0.000 | 0.667 | 1.000 |
| memory_retrieval | 3 | 0.856 | 0.000 | 0.722 | 0.889 |
| context_compression | 2 | 0.820 | 0.000 | 0.667 | 1.000 |
| redblue_repair | 3 | 0.889 | 0.000 | 0.556 | 1.000 |
| evaluation | 5 | 0.901 | 0.000 | 0.333 | 0.767 |
| multi_hop | 2 | 0.953 | 0.000 | 0.000 | 0.667 |
| llm_backend | 3 | 0.878 | 0.000 | 0.611 | 0.889 |
| engineering_tradeoff | 5 | 0.933 | 0.000 | 0.333 | 0.767 |
| reliability | 2 | 0.900 | 0.000 | 0.500 | 1.000 |
| rag_system | 2 | 0.872 | 0.000 | 0.500 | 1.000 |

### full
| domain | n | judge | hallucination | weak support | repair precision |
|---|---:|---:|---:|---:|---:|
| citation_verification | 3 | 0.889 | 0.000 | 0.556 | 1.000 |
| agent_orchestration | 5 | 0.801 | 0.000 | 0.667 | 1.000 |
| memory_retrieval | 3 | 0.856 | 0.000 | 0.722 | 0.889 |
| context_compression | 2 | 0.820 | 0.000 | 0.667 | 1.000 |
| redblue_repair | 3 | 0.889 | 0.000 | 0.556 | 1.000 |
| evaluation | 5 | 0.901 | 0.000 | 0.333 | 0.767 |
| multi_hop | 2 | 0.953 | 0.000 | 0.000 | 0.667 |
| llm_backend | 3 | 0.878 | 0.000 | 0.611 | 0.889 |
| engineering_tradeoff | 5 | 0.933 | 0.000 | 0.333 | 0.767 |
| reliability | 2 | 0.900 | 0.000 | 0.500 | 1.000 |
| rag_system | 2 | 0.872 | 0.000 | 0.500 | 1.000 |


## Multi-Hop And Hotpot Subsets

- `baseline` multi-hop: n=13, judge=0.778, repair_precision=0.000
- `baseline` hotpot-style: n=6, judge=0.769, repair_precision=0.000
- `memory` multi-hop: n=13, judge=0.778, repair_precision=0.000
- `memory` hotpot-style: n=6, judge=0.769, repair_precision=0.000
- `compression` multi-hop: n=13, judge=0.778, repair_precision=0.000
- `compression` hotpot-style: n=6, judge=0.769, repair_precision=0.000
- `verifier` multi-hop: n=13, judge=0.876, repair_precision=0.000
- `verifier` hotpot-style: n=6, judge=0.858, repair_precision=0.000
- `redblue` multi-hop: n=13, judge=0.889, repair_precision=0.923
- `redblue` hotpot-style: n=6, judge=0.880, repair_precision=0.889
- `full` multi-hop: n=13, judge=0.889, repair_precision=0.923
- `full` hotpot-style: n=6, judge=0.880, repair_precision=0.889

## Repair Action Distribution

- `baseline`: none
- `memory`: none
- `compression`: none
- `verifier`: none
- `redblue`: add=17, delete=10, modify=49
- `full`: add=17, delete=10, modify=49

## Integrity Report

- Dataset summary: `{'path': 'data\\benchmarks\\researchbench.jsonl', 'case_count': 35, 'answer_type_counts': {'factual_explanation': 29, 'multi_hop_reasoning': 1, 'risk_analysis': 2, 'technical_comparison': 1, 'solution_design': 2}, 'domain_counts': {'citation_verification': 3, 'agent_orchestration': 5, 'memory_retrieval': 3, 'context_compression': 2, 'redblue_repair': 3, 'evaluation': 5, 'multi_hop': 2, 'llm_backend': 3, 'engineering_tradeoff': 5, 'reliability': 2, 'rag_system': 2}, 'difficulty_counts': {'easy': 11, 'medium': 19, 'hard': 5}, 'suite_source_counts': {'researchbench': 35}, 'average_required_hops': 1.4, 'multi_hop_count': 13, 'hotpot_style_count': 6}`
- Suite source counts: `{'researchbench': 35}`
- Experiment artifacts: `{'baseline': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_baseline.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_vector_baseline.npz', 'plan_dir': 'reports\\plans\\baseline'}, 'memory': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_memory.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_vector_memory.npz', 'plan_dir': 'reports\\plans\\memory'}, 'compression': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_compression.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_vector_compression.npz', 'plan_dir': 'reports\\plans\\compression'}, 'verifier': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_verifier.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_vector_verifier.npz', 'plan_dir': 'reports\\plans\\verifier'}, 'redblue': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_redblue.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_vector_redblue.npz', 'plan_dir': 'reports\\plans\\redblue'}, 'full': {'memory_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_full.sqlite3', 'vector_path': 'reports\\final\\final_sprint_check\\memory\\researchbench_vector_full.npz', 'plan_dir': 'reports\\plans\\full'}}`