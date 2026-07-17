# Retrieval Quality Evaluation

- Generated (UTC): `2026-07-17T08:26:53.995028+00:00`
- Benchmark: `data/benchmarks/retrieval_holdout_v1.jsonl`
- Benchmark SHA-256: `5426679e2159266880441d3c1731542897ef9c926a20f0bb34b8f3419d05b287`
- Corpus: `data/corpus/offline_corpus.jsonl`
- Corpus SHA-256: `d8dbd6d6cdb44f7abbb28879c4b980827b703c8ea40908fd72880baa9f2b1cc0`
- Cases: **80**
- Cutoffs: `K=1, K=3, K=5`
- Embedding provider: `openai_compatible`

The benchmark uses frozen questions and their `required_sources` labels. Web search is disabled, so this measures local retrieval only. Check the benchmark documentation before interpreting a development set as a held-out result.

## Mode comparison

| Mode | Recall@1 | Recall@3 | Recall@5 | Hit@5 | All relevant@5 | MRR@5 | nDCG@5 | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.315 | 0.573 | 0.666 | 0.738 | 0.588 | 0.585 | 0.573 | 33 |
| vector | 0.606 | 0.866 | 0.920 | 0.988 | 0.838 | 0.915 | 0.878 | 13 |
| hybrid | 0.465 | 0.786 | 0.860 | 0.925 | 0.787 | 0.783 | 0.772 | 17 |

## Hybrid breakdown

### By difficulty

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| easy | 15 | 0.933 | 0.933 | 0.822 |
| hard | 35 | 0.810 | 0.657 | 0.814 |
| medium | 30 | 0.883 | 0.867 | 0.726 |

### By domain

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| agent_orchestration | 10 | 0.917 | 0.800 | 0.883 |
| citation_verification | 7 | 0.952 | 0.857 | 0.886 |
| context_compression | 4 | 1.000 | 1.000 | 1.000 |
| engineering_tradeoff | 10 | 0.817 | 0.700 | 0.850 |
| evaluation | 15 | 0.678 | 0.600 | 0.667 |
| llm_backend | 4 | 1.000 | 1.000 | 0.688 |
| memory_retrieval | 12 | 0.875 | 0.833 | 0.625 |
| multi_hop | 4 | 1.000 | 1.000 | 1.000 |
| rag_system | 2 | 0.750 | 0.500 | 1.000 |
| redblue_repair | 6 | 0.889 | 0.833 | 0.917 |
| reliability | 6 | 0.889 | 0.833 | 0.556 |

### By required_hops

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| 1 | 40 | 0.900 | 0.900 | 0.728 |
| 2 | 25 | 0.880 | 0.800 | 0.867 |
| 3 | 11 | 0.758 | 0.455 | 0.848 |
| 4 | 3 | 0.833 | 0.667 | 0.833 |
| 5 | 1 | 0.000 | 0.000 | 0.000 |

### By language

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| en | 33 | 0.909 | 0.818 | 0.816 |
| zh | 47 | 0.826 | 0.766 | 0.760 |

### By query_style

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| colloquial | 2 | 1.000 | 1.000 | 1.000 |
| comparison | 4 | 0.708 | 0.500 | 0.708 |
| contrast | 6 | 1.000 | 1.000 | 0.917 |
| definition | 8 | 0.875 | 0.875 | 0.729 |
| long_query | 4 | 0.625 | 0.500 | 0.500 |
| multi_hop | 19 | 0.860 | 0.684 | 0.912 |
| negative | 10 | 0.967 | 0.900 | 0.753 |
| paraphrase | 12 | 0.917 | 0.917 | 0.778 |
| question | 1 | 0.000 | 0.000 | 0.000 |
| scenario | 14 | 0.821 | 0.786 | 0.732 |

## Hybrid failure cases at K=5

| Case | Missing labels | Retrieved ids | Question |
|---|---|---|---|
| rh_010 | llm_judge | citation_tracking, textrank_context, sqlite_memory, hybrid_memory_design, hallucination_detection | 如果让模型给研究报告打分，除事实正确外还应观察覆盖率、引用和可用性吗？ |
| rh_012 | cohens_d | structured_outputs, red_blue_repair, sqlite_memory, agent_planning, sqlite_vector_tradeoffs | 两个 Agent 版本的分数差了 0.1，但这个差异在实践中究竟大不大，应该补充哪个标准化量？ |
| rh_023 | hybrid_memory_design | vector_database_limits, vector_retrieval, sqlite_vector_tradeoffs, structured_outputs, red_blue_repair | Agent 记忆层怎样同时保留规范记录、语义召回和原始证据溯源？ |
| rh_035 | cohens_d | llm_judge, hotpotqa_multihop, bootstrap_ci, researchbench_design, citation_tracking | What statistic expresses a pipeline improvement in standard-deviation units rather than raw score points? |
| rh_042 | sqlite_memory | vector_database_limits, sqlite_vector_tradeoffs, vector_retrieval, hybrid_memory_design, textrank_context | 如果既要保存结构化历史记录，又要按语义找回相似证据，持久层和向量索引怎样分工？ |
| rh_049 | structured_outputs | sqlite_memory, sqlite_vector_tradeoffs, hybrid_memory_design, failure_modes, offline_first | 想让每次运行可复现、每个中间结果可检查，为什么需要 SQLite 事件记录以及类型化输出？ |
| rh_050 | failure_modes, resume_alignment | hallucination_detection, citation_tracking, sqlite_memory, hybrid_memory_design, hotpotqa_multihop | 系统已经会生成答案，但简历仍缺可信度；应该怎样用测试指标和可定位代码把 Demo 变成可验证项目？ |
| rh_057 | llm_judge | vector_database_limits, cohens_d, researchbench_design, hybrid_memory_design, sqlite_vector_tradeoffs | 比较 baseline 和 full pipeline 时，需要同时说明多维评分与标准化效应量，分别从哪里得到？ |
| rh_058 | structured_outputs | technical_blog, resume_alignment, citation_tracking, researchbench_design, textrank_context | 研究结果要经得起面试追问，怎样把结构化实验产物转化成一篇可讲清取舍的技术文章？ |
| rh_061 | dag_orchestration | asyncio_semaphore, citation_tracking, agent_planning, sqlite_vector_tradeoffs, red_blue_repair | How should a planner's dependency graph and a semaphore work together when five searches are independent but the provider allows only two concurrent calls? |
| rh_065 | hotpotqa_multihop | researchbench_design, llm_judge, hallucination_detection, llm_backend, failure_modes | Why should benchmark design include labelled multi-document questions before an LLM judge scores final reports? |
| rh_070 | hallucination_detection | textrank_context, citation_tracking, sqlite_vector_tradeoffs, vector_database_limits, red_blue_repair | Connect context compression, citation lineage, and claim checking: what breaks if a compressor removes the exact quoted span? |
| rh_074 | technical_blog | resume_alignment, sqlite_vector_tradeoffs, structured_outputs, hybrid_memory_design, researchbench_design | Why is a one-question showcase insufficient for a credible resume, and what dataset and documentation artifacts address that weakness? |
| rh_075 | failure_modes, llm_backend | vector_database_limits, cohens_d, offline_first, sqlite_vector_tradeoffs, vector_retrieval | Compare a deterministic local baseline with a real-provider run: what architectural boundary allows both, and what reliability risks still require explicit testing? |
| rh_077 | agent_planning, asyncio_semaphore | citation_tracking, textrank_context, sqlite_memory, hybrid_memory_design, hallucination_detection | 系统要回答一个跨来源问题：先拆任务、并发检索、保存证据、最后检查引用。对应的四类工程机制是什么？ |
| rh_079 | hallucination_detection, textrank_context | hybrid_memory_design, red_blue_repair, structured_outputs, agent_planning, failure_modes | 既要节省上下文，又要避免无依据结论，并在发现问题后留下修复记录，需要串起哪些三个模块？ |
| rh_080 | bootstrap_ci, cohens_d, hotpotqa_multihop, llm_judge, researchbench_design | structured_outputs, red_blue_repair, sqlite_memory, agent_planning, sqlite_vector_tradeoffs | 请设计一套不夸大结论的 Agent 评测叙事：数据集要覆盖多跳，结果要有不确定性，差异要有实践效应量，模型评分不能当真值。 |

## Interpretation boundary

These figures are a deterministic regression baseline for this small curated corpus, not a production-search SLA or proof of general semantic retrieval quality. The hashing-vector ablation is educational; a production system should repeat the same evaluation with a real embedding model and a larger independently labelled dataset.
