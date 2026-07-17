# Retrieval Quality Evaluation

- Generated (UTC): `2026-07-17T08:24:48.246508+00:00`
- Benchmark: `data/benchmarks/retrieval_holdout_v1.jsonl`
- Benchmark SHA-256: `5426679e2159266880441d3c1731542897ef9c926a20f0bb34b8f3419d05b287`
- Corpus: `data/corpus/offline_corpus.jsonl`
- Corpus SHA-256: `d8dbd6d6cdb44f7abbb28879c4b980827b703c8ea40908fd72880baa9f2b1cc0`
- Cases: **80**
- Cutoffs: `K=1, K=3, K=5`
- Embedding provider: `hashing`

The benchmark uses frozen questions and their `required_sources` labels. Web search is disabled, so this measures local retrieval only. Check the benchmark documentation before interpreting a development set as a held-out result.

## Mode comparison

| Mode | Recall@1 | Recall@3 | Recall@5 | Hit@5 | All relevant@5 | MRR@5 | nDCG@5 | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.315 | 0.573 | 0.666 | 0.738 | 0.588 | 0.585 | 0.573 | 33 |
| vector | 0.058 | 0.225 | 0.371 | 0.500 | 0.225 | 0.239 | 0.246 | 62 |
| hybrid | 0.290 | 0.532 | 0.644 | 0.713 | 0.562 | 0.549 | 0.543 | 35 |

## Hybrid breakdown

### By difficulty

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| easy | 15 | 0.733 | 0.733 | 0.606 |
| hard | 35 | 0.643 | 0.457 | 0.663 |
| medium | 30 | 0.600 | 0.600 | 0.387 |

### By domain

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| agent_orchestration | 10 | 0.867 | 0.700 | 0.683 |
| citation_verification | 7 | 0.667 | 0.571 | 0.600 |
| context_compression | 4 | 0.750 | 0.750 | 0.750 |
| engineering_tradeoff | 10 | 0.367 | 0.300 | 0.400 |
| evaluation | 15 | 0.478 | 0.400 | 0.467 |
| llm_backend | 4 | 1.000 | 1.000 | 0.688 |
| memory_retrieval | 12 | 0.792 | 0.750 | 0.528 |
| multi_hop | 4 | 0.500 | 0.500 | 0.500 |
| rag_system | 2 | 0.750 | 0.500 | 1.000 |
| redblue_repair | 6 | 0.667 | 0.667 | 0.667 |
| reliability | 6 | 0.556 | 0.333 | 0.297 |

### By required_hops

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| 1 | 40 | 0.675 | 0.675 | 0.468 |
| 2 | 25 | 0.600 | 0.480 | 0.575 |
| 3 | 11 | 0.727 | 0.455 | 0.803 |
| 4 | 3 | 0.500 | 0.333 | 0.667 |
| 5 | 1 | 0.000 | 0.000 | 0.000 |

### By language

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| en | 33 | 0.894 | 0.788 | 0.816 |
| zh | 47 | 0.468 | 0.404 | 0.361 |

### By query_style

| Group | Cases | Recall@5 | All relevant@5 | MRR@5 |
|---|---:|---:|---:|---:|
| colloquial | 2 | 0.500 | 0.500 | 0.500 |
| comparison | 4 | 0.458 | 0.250 | 0.458 |
| contrast | 6 | 0.917 | 0.833 | 0.631 |
| definition | 8 | 0.750 | 0.750 | 0.604 |
| long_query | 4 | 0.375 | 0.250 | 0.375 |
| multi_hop | 19 | 0.658 | 0.474 | 0.702 |
| negative | 10 | 0.767 | 0.700 | 0.603 |
| paraphrase | 12 | 0.583 | 0.583 | 0.361 |
| question | 1 | 0.000 | 0.000 | 0.000 |
| scenario | 14 | 0.607 | 0.571 | 0.518 |

## Hybrid failure cases at K=5

| Case | Missing labels | Retrieved ids | Question |
|---|---|---|---|
| rh_004 | sqlite_memory | llm_backend, asyncio_semaphore, agent_planning, dag_orchestration, vector_database_limits | 我希望程序重启后还能追查某次运行的任务、证据和结论，轻量持久层应该保存什么？ |
| rh_006 | textrank_context | asyncio_semaphore, dag_orchestration, resume_alignment, red_blue_repair, sqlite_memory | 上下文太长需要压缩，但后续还要核对原文引句；哪种图排序方法适合挑选重要句子？ |
| rh_007 | citation_tracking | red_blue_repair, agent_planning, dag_orchestration, hallucination_detection, offline_first | 报告中的一句话怎样一路定位到具体文档、切片和原始引文，而不是只显示一个链接？ |
| rh_010 | llm_judge | citation_tracking, textrank_context, sqlite_memory, hybrid_memory_design, hallucination_detection | 如果让模型给研究报告打分，除事实正确外还应观察覆盖率、引用和可用性吗？ |
| rh_011 | bootstrap_ci | agent_planning, red_blue_repair, asyncio_semaphore, hotpotqa_multihop, researchbench_design | 样本不多时，怎样通过重复重采样给平均指标附上不确定性区间？ |
| rh_012 | cohens_d | structured_outputs, red_blue_repair, sqlite_memory, agent_planning, sqlite_vector_tradeoffs | 两个 Agent 版本的分数差了 0.1，但这个差异在实践中究竟大不大，应该补充哪个标准化量？ |
| rh_013 | researchbench_design | offline_first, sqlite_memory, dag_orchestration, structured_outputs, agent_planning | 自建研究型问答测试集时，每条样本除了问题还要标注哪些正确要点、证据和禁止结论？ |
| rh_014 | hotpotqa_multihop | cohens_d, dag_orchestration, sqlite_memory, hybrid_memory_design, technical_blog | 什么样的问题必须串联两份以上材料才能回答，可用于考察分解、检索与综合？ |
| rh_017 | failure_modes | sqlite_vector_tradeoffs, sqlite_memory, hybrid_memory_design, llm_judge, llm_backend | 别只怪 prompt：DeepResearch 系统还可能因为规划浅、证据重复或压缩过度而怎么失败？ |
| rh_018 | technical_blog | textrank_context, citation_tracking, hybrid_memory_design, red_blue_repair, dag_orchestration | 项目技术文章如何从问题、设计取舍、实验和失败案例讲清楚工程能力？ |
| rh_019 | resume_alignment | asyncio_semaphore, failure_modes, citation_tracking, bootstrap_ci, dag_orchestration | 简历里的项目数字怎样做到可复现、能指向代码，而不是听起来像包装？ |
| rh_023 | hybrid_memory_design | vector_database_limits, vector_retrieval, sqlite_vector_tradeoffs, structured_outputs, sqlite_memory | Agent 记忆层怎样同时保留规范记录、语义召回和原始证据溯源？ |
| rh_035 | cohens_d | llm_judge, hotpotqa_multihop, bootstrap_ci, researchbench_design, citation_tracking | What statistic expresses a pipeline improvement in standard-deviation units rather than raw score points? |
| rh_041 | citation_tracking, hallucination_detection | dag_orchestration, resume_alignment, red_blue_repair, llm_backend, hotpotqa_multihop | 一份可审计报告为什么既要记录证据链接，又要判断每条结论是否真的被这些证据支持？ |
| rh_042 | sqlite_memory | vector_database_limits, sqlite_vector_tradeoffs, vector_retrieval, hybrid_memory_design, textrank_context | 如果既要保存结构化历史记录，又要按语义找回相似证据，持久层和向量索引怎样分工？ |
| rh_043 | asyncio_semaphore | sqlite_memory, dag_orchestration, agent_planning, sqlite_vector_tradeoffs, offline_first | 研究任务有依赖关系且外部接口有并发上限，如何同时安排拓扑批次和流量控制？ |
| rh_045 | hallucination_detection, red_blue_repair | offline_first, llm_backend, agent_planning, llm_judge, resume_alignment | 先发现无支持陈述，再由攻击与修复角色决定删除或降级措辞，这两个阶段分别解决什么问题？ |
| rh_049 | structured_outputs | sqlite_memory, sqlite_vector_tradeoffs, hybrid_memory_design, offline_first, failure_modes | 想让每次运行可复现、每个中间结果可检查，为什么需要 SQLite 事件记录以及类型化输出？ |
| rh_050 | failure_modes, resume_alignment | hallucination_detection, citation_tracking, sqlite_memory, hybrid_memory_design, hotpotqa_multihop | 系统已经会生成答案，但简历仍缺可信度；应该怎样用测试指标和可定位代码把 Demo 变成可验证项目？ |
| rh_051 | resume_alignment, technical_blog | sqlite_memory, sqlite_vector_tradeoffs, dag_orchestration, hybrid_memory_design, vector_database_limits | 技术博客和简历应该如何分工：前者展开设计与失败，后者只保留可复现结果和工程贡献？ |
| rh_056 | bootstrap_ci, llm_judge | citation_tracking, hallucination_detection, failure_modes, dag_orchestration, resume_alignment | 模型裁判的平均分上升后，为什么还要用置信区间判断稳定性，且不能把裁判当绝对真理？ |
| rh_057 | llm_judge | vector_database_limits, cohens_d, researchbench_design, hybrid_memory_design, sqlite_vector_tradeoffs | 比较 baseline 和 full pipeline 时，需要同时说明多维评分与标准化效应量，分别从哪里得到？ |
| rh_058 | structured_outputs, technical_blog | researchbench_design, vector_database_limits, vector_retrieval, failure_modes, dag_orchestration | 研究结果要经得起面试追问，怎样把结构化实验产物转化成一篇可讲清取舍的技术文章？ |
| rh_059 | agent_planning, hotpotqa_multihop | vector_retrieval, vector_database_limits, sqlite_vector_tradeoffs, researchbench_design, failure_modes | 多跳任务不仅是答案更长：它为什么要求规划拆分并从多来源汇总证据？ |
| rh_060 | failure_modes | llm_backend, vector_database_limits, llm_judge, hotpotqa_multihop, offline_first | 离线实验能消除网络波动，但仍可能有评测偏差和错误规划；这两类可靠性边界如何区分？ |
| rh_061 | dag_orchestration | asyncio_semaphore, citation_tracking, agent_planning, red_blue_repair, sqlite_vector_tradeoffs | How should a planner's dependency graph and a semaphore work together when five searches are independent but the provider allows only two concurrent calls? |
| rh_065 | hotpotqa_multihop | researchbench_design, llm_judge, hallucination_detection, llm_backend, failure_modes | Why should benchmark design include labelled multi-document questions before an LLM judge scores final reports? |
| rh_070 | hallucination_detection | textrank_context, citation_tracking, sqlite_vector_tradeoffs, vector_database_limits, red_blue_repair | Connect context compression, citation lineage, and claim checking: what breaks if a compressor removes the exact quoted span? |
| rh_071 | dag_orchestration | agent_planning, failure_modes, llm_backend, asyncio_semaphore, citation_tracking | A research run hangs after one upstream task fails. Which workflow model should expose blocked descendants, and which known failure category does this prevent from being hidden? |
| rh_074 | technical_blog | resume_alignment, sqlite_vector_tradeoffs, structured_outputs, hybrid_memory_design, researchbench_design | Why is a one-question showcase insufficient for a credible resume, and what dataset and documentation artifacts address that weakness? |
| rh_075 | failure_modes, llm_backend | vector_database_limits, cohens_d, offline_first, sqlite_vector_tradeoffs, asyncio_semaphore | Compare a deterministic local baseline with a real-provider run: what architectural boundary allows both, and what reliability risks still require explicit testing? |
| rh_077 | agent_planning, asyncio_semaphore | citation_tracking, textrank_context, sqlite_memory, hybrid_memory_design, hallucination_detection | 系统要回答一个跨来源问题：先拆任务、并发检索、保存证据、最后检查引用。对应的四类工程机制是什么？ |
| rh_078 | dag_orchestration, failure_modes, resume_alignment, structured_outputs | citation_tracking, technical_blog, agent_planning, researchbench_design, textrank_context | 我不想要一个只会输出漂亮答案的 demo；请找出能证明它具备任务编排、结构化中间态、故障分析和简历可复现性的材料。 |
| rh_079 | hallucination_detection, red_blue_repair, textrank_context | hotpotqa_multihop, bootstrap_ci, offline_first, failure_modes, dag_orchestration | 既要节省上下文，又要避免无依据结论，并在发现问题后留下修复记录，需要串起哪些三个模块？ |
| rh_080 | bootstrap_ci, cohens_d, hotpotqa_multihop, llm_judge, researchbench_design | structured_outputs, red_blue_repair, sqlite_memory, agent_planning, sqlite_vector_tradeoffs | 请设计一套不夸大结论的 Agent 评测叙事：数据集要覆盖多跳，结果要有不确定性，差异要有实践效应量，模型评分不能当真值。 |

## Interpretation boundary

These figures are a deterministic regression baseline for this small curated corpus, not a production-search SLA or proof of general semantic retrieval quality. The hashing-vector ablation is educational; a production system should repeat the same evaluation with a real embedding model and a larger independently labelled dataset.
