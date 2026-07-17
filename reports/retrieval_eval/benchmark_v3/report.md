# Retrieval Quality Evaluation

- Generated (UTC): `2026-07-16T18:11:49.104674+00:00`
- Benchmark: `data/benchmarks/researchbench.jsonl`
- Benchmark SHA-256: `a3e1015d3b302780b8ec3f666d176b292810b1fee5127aa7f7f3d82c24a49ef9`
- Corpus: `data/corpus/offline_corpus.jsonl`
- Corpus SHA-256: `d8dbd6d6cdb44f7abbb28879c4b980827b703c8ea40908fd72880baa9f2b1cc0`
- Cases: **35**
- Cutoffs: `K=1, K=3, K=5`
- Embedding provider: `hashing`

The benchmark reuses frozen ResearchBench questions and their `required_sources` labels. Web search is disabled, so this measures local retrieval only.

## Mode comparison

| Mode | Recall@1 | Recall@3 | Recall@5 | Hit@5 | All relevant@5 | MRR@5 | nDCG@5 | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.633 | 0.786 | 0.843 | 0.943 | 0.743 | 0.843 | 0.796 | 9 |
| vector | 0.229 | 0.529 | 0.610 | 0.686 | 0.543 | 0.432 | 0.457 | 16 |
| hybrid | 0.662 | 0.786 | 0.843 | 0.943 | 0.743 | 0.852 | 0.804 | 9 |

## Hybrid breakdown

### By difficulty

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| easy | 11 | 0.864 | 0.818 | 0.841 |
| hard | 5 | 0.800 | 0.600 | 0.767 |
| medium | 19 | 0.842 | 0.737 | 0.882 |

### By domain

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| agent_orchestration | 5 | 0.900 | 0.800 | 0.850 |
| citation_verification | 3 | 0.500 | 0.333 | 0.500 |
| context_compression | 2 | 0.750 | 0.500 | 1.000 |
| engineering_tradeoff | 5 | 0.800 | 0.800 | 0.800 |
| evaluation | 5 | 0.867 | 0.800 | 1.000 |
| llm_backend | 3 | 1.000 | 1.000 | 1.000 |
| memory_retrieval | 3 | 1.000 | 1.000 | 0.778 |
| multi_hop | 2 | 1.000 | 1.000 | 0.750 |
| rag_system | 2 | 0.583 | 0.000 | 1.000 |
| redblue_repair | 3 | 0.833 | 0.667 | 0.750 |
| reliability | 2 | 1.000 | 1.000 | 1.000 |

### By required_hops

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| 1 | 22 | 0.932 | 0.909 | 0.920 |
| 2 | 12 | 0.694 | 0.500 | 0.715 |
| 3 | 1 | 0.667 | 0.000 | 1.000 |

## Hybrid failure cases at K=5

| Case | Missing labels | Retrieved ids | Question |
|---|---|---|---|
| rb_007 | hallucination_detection | sqlite_vector_tradeoffs, resume_alignment, bootstrap_ci, vector_retrieval, agent_planning | What is claim-evidence alignment? |
| rb_022 | structured_outputs | hybrid_memory_design, hallucination_detection, technical_blog, failure_modes, researchbench_design | Design a verification trace for unsupported claims. |
| rb_025 | textrank_context | failure_modes, vector_database_limits, llm_judge, dag_orchestration, hotpotqa_multihop | Why can over-compression hurt research quality? |
| rb_026 | asyncio_semaphore | dag_orchestration, agent_planning, technical_blog, llm_judge, hotpotqa_multihop | How do topological batches enable concurrent execution? |
| rb_027 | bootstrap_ci, llm_judge | cohens_d, hybrid_memory_design, textrank_context, technical_blog, hallucination_detection | How would you evaluate baseline versus full pipeline? |
| rb_028 | failure_modes, resume_alignment | cohens_d, sqlite_vector_tradeoffs, agent_planning, red_blue_repair, offline_first | What is the difference between a demo agent and a real engineering project? |
| rb_032 | failure_modes | hallucination_detection, sqlite_memory, structured_outputs, red_blue_repair, hotpotqa_multihop | How can missing evidence be surfaced in a report? |
| rb_034 | dag_orchestration | agent_planning, citation_tracking, red_blue_repair, hybrid_memory_design, hotpotqa_multihop | Explain the data flow from user question to final report. |
| rb_035 | technical_blog | resume_alignment, agent_planning, textrank_context, red_blue_repair, cohens_d | What project artifacts should exist by the end? |

## Interpretation boundary

These figures are a deterministic regression baseline for this small curated corpus, not a production-search SLA or proof of general semantic retrieval quality. The hashing-vector ablation is educational; a production system should repeat the same evaluation with a real embedding model and a larger independently labelled dataset.
