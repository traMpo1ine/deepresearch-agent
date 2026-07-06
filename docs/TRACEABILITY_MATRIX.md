# 简历证据追踪矩阵

这份文档回答一个复试时很常见的问题：你简历里每一句 DeepResearch Agent 描述，到底对应哪些真实代码、测试、命令和实验产物？

使用方式：

```powershell
uv run python scripts/inspect_resume_evidence.py --list
uv run python scripts/inspect_resume_evidence.py --bullet orchestration
uv run python scripts/inspect_resume_evidence.py --bullet verifier_redblue --json
```

## 1. Orchestration

**可写说法：** 手写 Planner/DAGTaskGraph/TaskStateMachine/Coordinator，将复杂研究问题拆解为多 Agent 任务图，并使用 asyncio + Semaphore 执行拓扑批次任务；9 状态状态机记录 timeout、retry、replan 和 fallback trace。

**代码证据：**

- `src/deepresearch_agent/agents/planner.py`
- `src/deepresearch_agent/orchestration/dag.py`
- `src/deepresearch_agent/orchestration/state_machine.py`
- `src/deepresearch_agent/orchestration/coordinator.py`
- `src/deepresearch_agent/agents/base.py`

**测试证据：**

- `tests/unit/test_planner.py`
- `tests/unit/test_dag.py`
- `tests/unit/test_state_machine.py`
- `tests/unit/test_agent_run_interface.py`
- `tests/integration/test_mock_pipeline.py`
- `tests/unit/test_v3_mechanisms.py`

**怎么讲：** 最初顺序 pipeline 难以表达复杂研究任务里的依赖关系，所以先用 Planner 生成任务，再用 DAG 管依赖和拓扑批次，用状态机记录生命周期。V3 增加 `TIMED_OUT`、lightweight replan 和 fallback report，让失败路径也能被追踪。

**边界：** 这是本地离线任务编排，不是分布式调度系统。

## 2. Memory And Vector Retrieval

**可写说法：** 构建 SQLite 共享记忆与 numpy hashing vector index，结构化保存运行轨迹，实现 claim -> citation -> source chunk -> quote span 的可追溯链路。

**代码证据：**

- `src/deepresearch_agent/memory/sqlite_store.py`
- `src/deepresearch_agent/memory/vector_index.py`
- `scripts/inspect_memory.py`
- `scripts/inspect_report_trace.py`

**测试证据：**

- `tests/unit/test_sqlite_memory.py`
- `tests/unit/test_vector_index.py`
- `tests/unit/test_inspect_memory_script.py`
- `tests/unit/test_inspect_report_trace.py`

**怎么讲：** SQLite 负责保存可审计事实，numpy index 负责相似召回。这样以后即使把向量索引换成 FAISS/Chroma，证据审计链路仍然稳定。

**边界：** 当前 hashing vectorizer 是离线 baseline，不等同于真实 embedding 模型。

## 3. TextRank Compression

**可写说法：** 设计 TextRank 上下文压缩与引用保护机制，通过 L1 向量粗筛、L2 TextRank 句子排序、L3 citation quote 保留，降低上下文长度同时保留可验证证据。

**代码证据：**

- `src/deepresearch_agent/compression/textrank.py`
- `scripts/inspect_compression.py`
- `data/examples/compression_cases.jsonl`

**测试证据：**

- `tests/unit/test_compression.py`
- `tests/unit/test_compression_cases.py`

**怎么讲：** 压缩不能只追求短，因为后面 Verifier 需要原文 quote。这个模块的重点是减少上下文，同时不破坏引用验证链路。

**边界：** TextRank 是轻量启发式，后续可以做 LLM compressor 对照实验。

## 4. Verifier And Red-Blue

**可写说法：** 实现 Verifier + Red-Blue 对抗修复：Verifier 将长 claim 拆成 atomic claims 并输出多维 VerificationTrace；Blue Agent 执行 ADD/DELETE/MODIFY/VERIFY，并记录 repair loop 收敛、震荡和最大轮数停止原因。

**代码证据：**

- `src/deepresearch_agent/agents/verifier.py`
- `src/deepresearch_agent/agents/critic.py`
- `src/deepresearch_agent/redblue/blue_agent.py`
- `src/deepresearch_agent/redblue_convergence.py`
- `scripts/inspect_verification.py`
- `scripts/inspect_redblue.py`
- `scripts/inspect_redblue_convergence.py`

**测试证据：**

- `tests/unit/test_verifier.py`
- `tests/unit/test_verification_cases.py`
- `tests/unit/test_redblue.py`
- `tests/unit/test_redblue_cases.py`
- `tests/unit/test_redblue_fixtures.py`

**怎么讲：** 先做 fixed cases 和可观察 trace，再逐步优化算法。这样每个 claim 为什么 supported、partial、unsupported 或 contradicted 都能被解释，而不是只输出一个模糊分数。

**边界：** 当前 Verifier 是 heuristic，不是严格 NLI；Red-Blue repair 仍可能残留过度概括或旧记忆问题。

## 4.1 Formal LLM Verifier Benchmark

**可写说法：** 新增 formal LLM verifier benchmark，以 claim + evidence + quote 为输入调用 DeepSeek 二级判断，覆盖 supported/partial/unsupported/contradicted 四类 120 个 balanced cases，重复 3 轮共 360 次真实判断，accuracy 0.842、macro-F1 0.831、估算成本 RMB 0.05893803，并与端到端 offline/mock benchmark 隔离。

**代码证据：**

- `src/deepresearch_agent/evaluation/llm_verifier_smoke.py`
- `src/deepresearch_agent/evaluation/verifier_benchmark.py`
- `scripts/run_llm_verifier_smoke.py`
- `scripts/run_formal_verifier_benchmark.py`
- `scripts/build_llm_verifier_extended_cases.py`
- `data/examples/llm_verifier_cases.jsonl`
- `data/examples/llm_verifier_cases_extended.jsonl`
- `reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/report.md`
- `reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/aggregate.json`

**测试证据：**

- `tests/unit/test_llm_verifier_smoke.py`
- `tests/unit/test_formal_verifier_benchmark.py`

**怎么讲：** 这是对 heuristic verifier 边界的补强。默认 dry-run 不调用真实 API；只有显式 `--run-real` 且配置环境变量时才请求 DeepSeek。正式结果只评价 claim/evidence 分类能力，不进入 ResearchBench 端到端指标。

**边界：** LLM judge 也可能误判；该 benchmark 是 verifier 分类实验，不等于生产级 NLI，也不代表端到端 DeepResearch 质量。

## 5. Evaluation

**可写说法：** 自建 35 题 ResearchBench-style 离线评测集、10 题 adversarial suite 和 80 条 Red-Blue fixtures，覆盖 11 个 domain 和 HotpotQA-style 多跳子集，支持多配置对比、Bootstrap 95% CI、Cohen's d、repair_precision/coverage。

**代码证据：**

- `src/deepresearch_agent/evaluation/runner.py`
- `src/deepresearch_agent/evaluation/metrics.py`
- `scripts/run_eval.py`
- `configs/default.toml`

**测试证据：**

- `tests/unit/test_evaluation_runner.py`
- `tests/unit/test_evaluation_cases.py`
- `tests/unit/test_completion_check.py`

**怎么讲：** 评测先离线可复现，再配置化实验和完整性校验。所有指标只用于同一 offline/mock benchmark 内部比较，不夸大成线上效果。

**边界：** 数据集规模仍小，mock judge 不能代表真实用户场景泛化。

## 5.1 Extended ResearchBench Coverage

**可写说法：** 在冻结 35 题 ResearchBench 对比指标之外，新增并跑通 60 题 extended ResearchBench ablation，五类 answer_type 各 12 题；baseline judge mean 0.764 -> full 0.880，weak_support_rate 1.000 -> 0.431，full repair_precision 0.944、repair_coverage 1.000。

**代码证据：**

- `data/benchmarks/researchbench_extended.jsonl`
- `scripts/inspect_resume_metrics.py`
- `reports/experiments/20260705_020934_092414_researchbench_263e905e/summary.md`
- `reports/experiments/20260705_020934_092414_researchbench_263e905e/metrics.json`
- `reports/final/pre_resume_evidence_pack/index.md`
- `reports/final/pre_resume_evidence_pack/manifest.json`

**测试证据：**

- `tests/unit/test_extended_benchmark.py`

**怎么讲：** 原 35 题指标已经冻结，不静默改历史结果；60 题 extended 用来证明评测覆盖更均衡，并补了 baseline / verifier / redblue / full ablation，用来讲可信生成链路对弱支持 claim 的改进。

**边界：** extended ablation 是 offline/mock benchmark；没有把真实 DeepSeek 输出混入主指标，也没有覆盖 memory/compression 单独消融。

## 6. Structured Output And Claim Preflight

**可写说法：** 设计三层 JSON fallback 与 Claim Preflight，对 fenced/坏格式/缺字段 JSON 执行结构化解析恢复，并在 Writer 前做重复 claim、冲突 evidence 和过强断言的轻量消解。

**代码证据：**

- `src/deepresearch_agent/structured_output.py`
- `src/deepresearch_agent/claim_preflight.py`
- `scripts/inspect_structured_output.py`
- `src/deepresearch_agent/agents/writer.py`

**测试证据：**

- `tests/unit/test_structured_output.py`
- `tests/unit/test_claim_preflight.py`
- `tests/unit/test_writer.py`

**怎么讲：** 真实 LLM 输出经常不是严格 JSON，所以先做三层 parser fallback，并记录 parse_level 和 warnings。Claim Preflight 则是在正式 Verifier 之前做写前防御，先把明显重复、冲突提示和过强表达暴露出来。

**边界：** JSON fallback 只覆盖常见坏格式；Claim Preflight 是启发式写前防御，不替代 Verifier/NLI。

## 7. Web Demo App

**可写说法：** 构建 FastAPI + 静态前端本地 Demo，支持默认 evidence pack 展示、新问题 mock/offline run、状态轮询，以及报告、证据、验证、修复链路可视化。

**代码证据：**

- `src/deepresearch_agent/web/app.py`
- `src/deepresearch_agent/web/static/index.html`
- `src/deepresearch_agent/web/static/app.js`
- `scripts/run_demo_server.py`

**测试证据：**

- `tests/integration/test_web_demo.py`

**怎么讲：** 底层 Agent 链路已经稳定后，我没有重写系统，而是在现有 `build_showcase()` 和 Markdown/JSON 产物之上加了薄 Web 层。默认页面先加载 final evidence pack，保证演示稳定；新问题走 mock/offline run，避免现场误扣费；DeepSeek 只作为 provider smoke。

**边界：** 这是本地作品展示，不是线上多用户服务；运行状态保存在进程内存中，重启后不会保留 demo job 状态。

## 8. Local Corpus Profiles

**可写说法：** 构建 local corpus profile 模式，从本地 Markdown/TXT/HTML 资料生成 Searcher-compatible JSONL corpus，并在 Web Demo 中选择不同知识库 profile，增强企业知识库式 RAG 演示真实感。

**代码证据：**

- `src/deepresearch_agent/corpus_profiles.py`
- `scripts/build_corpus_profiles.py`
- `data/corpus_profiles/offline_agent_docs/agent_reliability.md`
- `data/corpus_profiles/resume_agent_docs/resume_story.md`
- `data/corpus_profiles/paper_reading_docs/paper_reading_workflow.md`
- `data/corpus/profiles/resume_agent_docs.jsonl`

**测试证据：**

- `tests/unit/test_corpus_profiles.py`
- `tests/integration/test_web_demo.py`

**怎么讲：** 这一步不做不稳定的全网搜索，而是先做本地知识库 RAG：资料目录可控，chunk/citation/quote 可追踪，面试现场更稳定。

**边界：** 当前 profile 是本地资料目录构建，不是线上上传、多租户知识库，也不声称覆盖全网。

## 复习建议

复习时不要直接背 bullet。按这个顺序：

1. 先跑 `inspect_resume_evidence.py --list` 看有哪些证据卡。
2. 每次只选一个 bullet，比如 `--bullet verifier_redblue`。
3. 打开对应源码和测试。
4. 跑卡片里的命令。
5. 最后用“怎么讲”和“边界”组织成自己的回答。
