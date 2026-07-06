# DeepResearch Agent 最终项目报告

## 1. 项目摘要

DeepResearch Agent 是一个面向复杂深度研究任务的多智能体协作系统。项目目标不是做一个简单 RAG demo，而是把一次研究任务拆成可观察、可追踪、可验证、可修复、可评测的工程流水线。

当前版本采用离线优先策略：mock LLM、本地 corpus、SQLite、numpy vector index、TextRank、heuristic verifier 和 mock LLM-as-Judge 都可以在本地复现。真实 LLM 后端保留为可选 smoke，不参与默认测试和正式 mock benchmark。

项目对应的核心能力：

- Planner / Searcher / Reader / Writer / Critic / Verifier / Blue Repair 多 Agent 协作。
- asyncio + Semaphore + DAG 拓扑批次执行。
- SQLite 共享记忆与 numpy 向量相似召回。
- TextRank 上下文压缩与 citation quote 保护。
- atomic claim verification、引用追踪、幻觉检测。
- Red-Blue 对抗修复，支持 ADD / DELETE / MODIFY / VERIFY。
- 三层 JSON fallback 和 Claim Preflight。
- 9 状态任务生命周期、timeout/replan/fallback trace。
- Red-Blue repair loop 收敛与震荡检测。
- ResearchBench-style 主集、adversarial suite、Bootstrap 95% CI、Cohen's d。
- Mock / OpenAI-compatible / DeepSeek / vLLM 后端适配骨架。

## 2. 系统架构

```text
User Question
  -> Planner
  -> DAGTaskGraph + TaskStateMachine
  -> Searcher / Reader
  -> SQLite Memory + Numpy Vector Index
  -> TextRank Compressor
  -> Writer
  -> Verifier
  -> Red/Critic
  -> Blue Repair
  -> Markdown/JSON Report
  -> Evaluation Runner
```

关键设计是把每一步都结构化：

- Planner 输出 `ResearchPlan` 和 `ResearchTask`。
- Reader 输出 `Evidence`，包含 source、chunk、quote、score、metadata。
- Writer 输出 `ResearchReport`，其中 `Claim` 绑定 citation ids。
- Verifier 输出 `VerificationTrace`，解释每条 atomic claim 的判断。
- Blue Repair 输出 `RepairAction`，记录修复动作和 before/after。
- Evaluation 输出 `EvaluationResult`，用于批量实验对比。

## 3. 核心模块完成情况

### 3.1 Orchestration

已完成：

- 统一 `BaseAgent.run(input, context) -> AgentResult` 包装。
- Coordinator 真实运行路径接入 `AgentResult`，并把 ok/error/latency/metadata 写入 SQLite agent_events。
- DAG 节点与依赖建模。
- 拓扑批次执行。
- 循环检测。
- 失败阻塞传播。
- 任务状态机。
- `TIMED_OUT` 第 9 状态。
- task timeout/retry、batch lightweight replan、global fallback report。
- asyncio + Semaphore 并发执行。

解决的问题：

- 复杂研究任务不能只靠顺序 pipeline。
- 并发任务需要明确依赖边界。
- 失败节点需要被记录，并阻塞下游依赖任务。
- 多 Agent 系统需要统一 trace，否则排查问题时无法知道哪个 Agent 在哪个阶段失败。
- 失败路径也要可观察，否则只能展示成功样例，无法解释 timeout、replan 和 fallback。

### 3.2 Search And Evidence

已完成：

- 本地 corpus 检索。
- 中文/英文 query expansion。
- lexical / hybrid score。
- Reader chunking 与 quote extraction。
- Evidence 去重和 metadata 保存。

解决的问题：

- Planner 拆得对不代表证据找得准。
- 中文问题很难直接命中英文离线语料。
- 报告里的 claim 必须能反查原文 quote。

### 3.3 Memory And Retrieval

已完成：

- SQLite 保存 runs、tasks、evidence、claims、reports、agent events。
- numpy hashing vector index 做相似 evidence 召回。
- vector hit 回表到 SQLite，拿到完整 source/chunk/quote。
- 损坏 vector index 自动重建。

设计理由：

- SQLite 负责审计链路。
- vector index 负责相似召回。
- 两者分离后，向量检索策略可以替换，但证据审计链路不变。

### 3.4 Compression

已完成：

- L1 embedding 粗过滤。
- L2 TextRank 句子排序。
- L3 citation quote preservation。
- fixed compression cases。

设计理由：

- 长 evidence 不能全部塞给 Writer。
- 普通摘要可能改写或丢掉引用原文。
- quote preservation 是后续 Verifier 能工作的前提。

### 3.5 Verifier

已完成：

- atomic claim split。
- best evidence selection。
- term overlap、quote overlap、source trust。
- contradiction cues。
- VerificationTrace。

设计理由：

- 长 claim 可能一半有证据、一半没证据。
- 直接整体判断会掩盖 partial support。
- heuristic verifier 虽然不是严格 NLI，但可解释、可复现、适合回归测试。

### 3.6 Red-Blue Repair

已完成：

- Red/Critic 输出 AttackFinding。
- Blue Agent 执行 ADD / DELETE / MODIFY / VERIFY。
- RepairAction 记录 before/after。
- RepairLoopTrace 记录每轮 finding、weak claim、repair action、fingerprint 和 stop reason。
- 80 条 Red-Blue fixtures。
- fixed learning cases 和 inspect CLI。
- 80 条 adversarial fixtures 的 before/after repair success 评测。

设计理由：

- 普通 self-reflection 不够工程化。
- Red-Blue 把“发现问题”和“修复问题”拆成结构化动作。
- 修复过程可测试、可统计、可复盘。
- 收敛/震荡检测能避免 repair loop 盲目固定轮数。

### 3.7 Evaluation

已完成：

- 35 题 ResearchBench-style 主集。
- 10 题 adversarial suite。
- baseline / memory / compression / verifier / redblue / full 多配置评测。
- judge mean、Bootstrap 95% CI、Cohen's d。
- weak_support_rate、atomic_support_rate、repair_precision、repair_coverage。
- repair_convergence_rate、repair_oscillation_rate、avg_repair_rounds。
- per_domain、multi_hop_subset、hotpot_style_subset。
- failure_cases 和 integrity_report。
- LLM-as-Judge 5 维度均值：factuality、coverage、citation_quality、structure、usefulness。

设计理由：

- 不能只展示几个好看的报告。
- 需要同一离线 benchmark 内的可复现对比。
- 指标必须明确边界，不能包装成线上效果。

## 4. 正式实验结果

### 4.0 Final Sprint Evidence Pack

- 入口：`reports/final/final_sprint_check/index.md`
- ResearchBench full：judge mean 0.880，95% CI `[0.858, 0.903]`，hallucination_rate 0.000，repair_precision 0.895，repair_coverage 1.000。
- Adversarial redblue：judge mean 0.920，95% CI `[0.893, 0.950]`，repair_precision 0.883，repair_coverage 1.000。
- Red-Blue fixtures：80 条，repair_success_before 0.425 -> repair_success_after 1.000。
- Structured JSON fallback：50 条，parse_success_rate 1.000，Level 1/2/3 = 6/11/33。

以下 V3 run id 保留为历史正式实验基线。

### 4.1 ResearchBench 主集

- Run id：`20260702_162345_148429_researchbench_21c535de`
- Dataset：`data/benchmarks/researchbench.jsonl`
- Cases：35
- Domains：11
- Multi-hop cases：13
- Hotpot-style cases：6
- Experiments：`baseline,memory,compression,verifier,redblue,full`

| experiment | judge | 95% CI | hallucination | weak support | atomic support | repair precision | repair coverage | convergence | oscillation |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.774 | [0.759, 0.788] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| verifier | 0.867 | [0.846, 0.887] | 0.105 | 0.667 | 0.471 | 0.000 | 0.000 | 1.000 | 0.000 |
| redblue | 0.878 | [0.858, 0.899] | 0.000 | 0.490 | 0.619 | 0.886 | 1.000 | 1.000 | 0.514 |
| full | 0.881 | [0.859, 0.903] | 0.000 | 0.490 | 0.619 | 0.886 | 1.000 | 1.000 | 0.514 |

解释：

- baseline 不启用 verifier，因此 weak_support_rate 为 1.000，表示 claim 没经过强验证。
- verifier 会暴露 weak/unsupported claim，所以 hallucination_rate 变得可见。
- redblue 在 verifier 基础上执行 repair，使 hallucination_rate 降到 0.000，并保留 repair action 记录。
- V3 额外记录 repair convergence / oscillation。oscillation 不为 0 是真实边界，表示启发式修复在部分 claim 上会重复 MODIFY。

### 4.2 Adversarial Suite

- Run id：`20260702_163315_852511_adversarial_f47f9b96`
- Dataset：`data/benchmarks/adversarial_researchbench.jsonl`
- Cases：10
- Multi-hop cases：7
- Experiments：`baseline,verifier,redblue`

| experiment | judge | 95% CI | hallucination | weak support | atomic support | repair precision | repair coverage | convergence | oscillation |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.791 | [0.772, 0.800] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| verifier | 0.907 | [0.880, 0.933] | 0.100 | 0.567 | 0.643 | 0.000 | 0.000 | 1.000 | 0.000 |
| redblue | 0.913 | [0.890, 0.940] | 0.000 | 0.433 | 0.736 | 0.933 | 1.000 | 1.000 | 0.300 |

解释：

- adversarial suite 覆盖 no citation、wrong citation、overclaim、contradiction、omission、vague claim、stale memory、over-compression。
- redblue repair action 分布为 `add=3, delete=2, modify=12`。
- failure cases 仍显示部分 prohibited claim cue 残留，说明 heuristic repair 还不能替代更强的 LLM/NLI verifier。

### 4.3 Structured Output / Red-Blue Fixture Checks

- Structured JSON fallback：50 条 corrupted-output cases，parse_success_rate 1.000，Level 1/2/3 分布为 6/11/33。
- Red-Blue fixtures：80 条 adversarial fixtures，repair_success_before 0.425，repair_success_after 1.000，action_accuracy 1.000，repair_precision 1.000，repair_coverage 1.000。
- Backend smoke matrix：默认只 smoke mock；OpenAI / DeepSeek / vLLM 在无 key 时 dry-run，不进入 ResearchBench 正式指标。

## 5. 运行与验收

推荐演示命令：

```powershell
uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？"
```

Showcase Pack 会生成 `llm_backend.md`，记录 backend、model、base url、env 配置、offline safety 和 run summary 中的后端字段。真实 LLM 后端只作为可选 smoke，不和 offline/mock benchmark 指标混写。

正式质量门：

```powershell
uv run ruff check src tests scripts
uv run pytest
uv run python -m compileall src scripts tests
uv run python scripts/check_project_completion.py
```

最近一次验证：

- ruff：passed。
- pytest：94 passed, 3 skipped。
- compileall：passed。
- completion check：passed。
- completion gate 覆盖 V3 orchestration failure trace、Red-Blue convergence trace、final report、resume evidence 等关键产物。

## 6. 结果边界

必须明确：

- 当前结果来自 offline/mock benchmark。
- Mock LLM-as-Judge 只用于比较项目内部配置。
- 不能把当前数字写成线上效果或真实用户场景。
- Heuristic Verifier 不是严格 NLI。
- Red-Blue 修复仍可能残留复杂 prohibited claim cue。

可以写：

```text
在自建 offline/mock ResearchBench-style 评测集上，对 baseline、verifier、redblue 等配置进行可复现实验对比。
```

不应该写：

```text
线上幻觉率降低到 0。
```

## 7. 复试讲解摘要

这个项目不是普通 RAG demo，而是一个离线可复现的 DeepResearch Agent。用户问题先由 Planner 拆成 DAG，Coordinator 用 asyncio + Semaphore 执行搜索和阅读任务，Evidence 写入 SQLite 和 numpy 向量索引。Writer 基于 TextRank 压缩后的证据生成带 citation 的报告，Verifier 把长 claim 拆成 atomic claims 并选择 best evidence，Red-Blue 模块再对弱支持 claim 做 DELETE/MODIFY/ADD 修复。最后用 35 题 ResearchBench-style 主集和 10 题 adversarial suite 做 mock/offline 评测，输出 judge score、Bootstrap CI、Cohen's d 和 repair precision/coverage。

项目最大的工程价值是：把 Agent 系统拆成了可追踪、可验证、可修复、可评测的链路，而不是只追求一次生成结果。

## 8. 后续增强

这些是可选增强，不影响当前项目完成态：

- 增加真实 LLM 单题 showcase，但不混入 offline 指标。
- 增加 LLM/NLI verifier 作为第二层验证。
- 扩大 ResearchBench，让每类 answer_type 至少 7 题。
- 增加更多中文 corpus 和中文 query expansion。
- 用 FAISS/Chroma 替换 NumpyVectorIndex 做对照实验。
- 做 notebook 或 Web UI 展示现有 Markdown/JSON 产物。
