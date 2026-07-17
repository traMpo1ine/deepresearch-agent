# DeepResearch Agent 项目完成过程总账

这个文件给未来复习用。它不是 README，也不是简历稿，而是记录“项目是怎么一步步做出来的”：每一阶段为什么做、遇到什么难题、怎么解决、为什么选择当前方案、以后怎么讲。

## 0. 项目目标如何确定

最初目标不是做一个普通 RAG demo，而是复现简历图里第二个项目的技术深度：面向复杂深度研究任务的多智能体协作系统，覆盖规划、执行、记忆、压缩、验证、对抗修复和评测。

核心取舍：

- 先离线可复现，再接真实 LLM。
- 先手写 DAG、状态机、Memory、Verifier，再考虑 LangGraph 等框架。
- 每个模块都要有 trace、测试和学习文档，避免只堆功能。
- 简历数字必须来自真实代码和离线实验，不提前写空泛指标。

最终项目一句话：

```text
DeepResearch Agent 不是直接生成答案，而是把研究任务拆成可观察、可追踪、可验证、可修复、可评测的工程流水线。
```

## 1. 工程骨架与异步编排

### 为什么做

复杂研究任务不适合顺序 pipeline。搜索、阅读、验证、修复之间有依赖关系，有些任务可以并发，有些任务必须等待上游证据。

### 做了什么

- 定义 `ResearchTask`、`ResearchPlan`、`Evidence`、`Claim`、`ResearchReport` 等核心 schema。
- 定义 `AgentResult` 和 `BaseAgent.run()` 统一 Agent 调用入口。
- 实现 `DAGTaskGraph`，支持依赖、拓扑批次、循环检测和阻塞传播。
- 实现 `TaskStateMachine`，管理 PENDING / READY / RUNNING / SUCCEEDED / FAILED / BLOCKED 等状态。
- `ResearchCoordinator` 使用 `asyncio.gather` 和 `Semaphore` 执行同层任务。

### 遇到的问题

早期如果只按顺序 mock 执行，无法讲清楚“复杂研究任务为什么需要编排”。此外，失败节点如果静默崩掉，下游任务会继续跑，最终 report 很难定位错误来源。

### 怎么解决

把任务执行抽象成 DAG 拓扑批次，并让状态机记录失败和阻塞原因。这样可以解释：DAG 管依赖，状态机管生命周期，Semaphore 管并发边界。

### 为什么不用 LangGraph

另一个横向项目已经基于 LangChain/LangGraph。这个项目的目标是学习底层机制，所以先手写 DAG 和状态机。后续如果迁移到 LangGraph，schema、memory、verifier 和 eval 仍然可以复用。

### 怎么验证

- `tests/unit/test_dag.py`
- `tests/unit/test_state_machine.py`
- `scripts/inspect_plan.py`
- `docs/generated/day02_plan.md`
- `tests/unit/test_agent_run_interface.py`

## 2. Planner / Searcher / Reader

### 为什么做

DeepResearch 的第一步不是回答，而是拆任务。Planner 决定研究路线，Searcher 和 Reader 决定证据地基。

### 做了什么

- Planner 保留 template 和 heuristic 两种模式。
- Heuristic Planner 支持 general、comparison、risk analysis、solution design。
- Searcher 使用本地 corpus，支持 query expansion 和 lexical/hybrid score。
- Reader 输出 chunk、quote、source metadata 和 dedupe key。

### 遇到的问题

“比较 SQLite 和向量数据库的优缺点”这类中文问题，Planner 能拆成 comparison，但 Searcher 找到的 evidence 会跑偏，导致 Writer 写出空泛 claim。

### 怎么解决

增加离线 query expansion，把“向量数据库 / 优缺点 / 比较”扩展到 `vector retrieval`、`embedding similarity`、`tradeoffs`、`hybrid memory design` 等英文语料关键词；同时补充 SQLite/vector/hybrid memory 相关 corpus。

### 为什么不用真实搜索或 LLM 改写

真实搜索会引入网络和排序波动；LLM 改写会掩盖检索机制。当前阶段优先学习可解释的信息检索基础。

### 怎么验证

- `scripts/run_research.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic`
- `docs/learning_searcher_grounding.md`
- `docs/BUILD_LOG.md` 中的 `Searcher Grounding`

## 3. SQLite Memory + Numpy Vector Index

### 为什么做

多 Agent 系统需要共享记忆。Searcher/Reader 产生的 evidence 不能只在内存里流转，必须能跨 Agent、跨运行追踪。

### 做了什么

- SQLite 保存 runs、tasks、evidence、claims、reports、agent_events、verification traces、repair actions。
- numpy hashing vector index 支持 add/search/save/load。
- vector index 返回 evidence id，再回 SQLite 取完整 quote/source/chunk。
- 增加损坏 `.npz` 自动重建，避免历史运行产物污染测试。
- 增加轻量 SQLite migration：`schema_migrations`、`PRAGMA user_version`、旧库缺列自动补齐。
- 增强 `inspect_memory.py`，支持查看 schema version、migrations、table counts、recent runs 和 evidence。

### 遇到的问题

一次测试失败来自默认加载的 `data/memory/vector_index.npz` 已损坏，`NumpyVectorIndex.load()` 读到坏 zip。这个问题说明测试环境不能依赖真实运行产物。

### 怎么解决

- Coordinator 加载 vector index 时，如果文件不存在或损坏，就 warning 并重建空索引。
- 集成测试使用 `tmp_path` 下的 SQLite/vector path。
- `.gitignore` 和 `clean_artifacts.py` 把 `data/memory/*` 视为运行产物。
- 对旧版 `verification_traces` 表使用 `_ensure_column()` 补齐 `atomic_results`，并记录 schema version。

### 为什么不用向量数据库

当前重点是学清楚 embedding、cosine similarity、top-k recall 和 id 回表机制。numpy 版本更透明，后续可替换 FAISS/Chroma，但 SQLite 审计链路仍保留。

### 怎么验证

- `scripts/inspect_memory_trace.py --case sqlite_vector_recall`
- `tests/unit/test_sqlite_memory.py`
- `tests/unit/test_vector_index.py`
- `tests/unit/test_memory_cases.py`
- `tests/unit/test_sqlite_memory.py::test_sqlite_memory_migrates_legacy_verification_trace_table`
- `scripts/inspect_memory.py --memory-path reports/showcase/final_check/memory.sqlite3 --schema --runs --limit 5`

## 4. TextRank 上下文压缩

### 为什么做

DeepResearch 会产生很多 evidence，全部塞给 Writer 会带来噪声和上下文成本。压缩的关键不是“越短越好”，而是不能丢 citation quote。

### 做了什么

- L1：embedding/向量粗过滤候选 evidence。
- L2：TextRank 句子图筛选重要句子。
- L3：强制保留 citation quote，保护后续验证链路。
- 增加 fixed compression cases 和 `inspect_compression.py`。

### 遇到的问题

普通摘要可能改写或丢掉 quote。一旦 quote 丢失，Writer 的 citation binding 和 Verifier 的 quote overlap 都会变弱。

### 怎么解决

把 quote preservation 放成硬约束：即使 `max_sentences=1`，也要优先保留被引用的原文 quote。

### 为什么不用 LLM summarizer

LLM summarizer 可能改写证据原文，且输出不稳定。TextRank 虽简单，但离线、可解释、可测试。

### 怎么验证

- `scripts/inspect_compression.py --case quote_preservation`
- `scripts/inspect_compression.py --case multi_quote_preservation --json`
- `tests/unit/test_compression_cases.py`

## 5. Writer / Verifier / Citation Trace

### 为什么做

研究报告不能只是自然语言答案。每个关键 claim 必须绑定 citation，并能解释它是否被 evidence 支持。

### 做了什么

- Writer 输出 Markdown 和 JSON。
- `Claim` 绑定 citation_ids。
- Verifier 将长 claim 拆成 atomic claims。
- 每个 atomic claim 选择 best evidence，输出 term overlap、quote overlap、missing terms、decision reason。
- 状态支持 SUPPORTED / PARTIAL / UNSUPPORTED / CONTRADICTED。
- `inspect_report_trace.py` 可从 report JSON 直接查看 claim -> citation -> evidence -> verification trace -> repair action。

### 遇到的问题

如果只对整句 claim 做 overlap，很容易把“部分支持”误判成“完全支持”。例如一句话里前半句有证据，后半句没有证据，整体状态不能是 supported。

### 怎么解决

做 atomic claim verification：先拆小，再分别验证，最后聚合。任一 contradicted 则整体 contradicted；全部 supported 才 supported；混合结果为 partial。

### 为什么不直接用 LLM-as-Verifier

LLM verifier 输出受模型、prompt、温度影响，不适合做早期回归测试。当前 heuristic verifier 可解释、可复现，后续可以作为 LLM/NLI verifier 的 baseline。

### 怎么验证

- `data/examples/verification_cases.jsonl`
- `scripts/inspect_verification.py --case mixed_atomic`
- `tests/unit/test_verification_cases.py`
- `docs/generated/day03_verifier_trace.md`
- `scripts/inspect_report_trace.py --report-json reports/showcase/final_check/report.json`

## 6. Red-Blue 对抗修复

### 为什么做

普通 self-reflection 太像一句提示词，难以测试和审计。Red-Blue 把“发现问题 -> 修复问题”变成结构化工程动作。

### 做了什么

- Red/Critic 输出 `AttackFinding`：category、severity、target、reason、suggested_check。
- Blue Agent 执行 ADD / DELETE / MODIFY / VERIFY。
- `RepairAction` 记录 target、before、after、reason。
- 建立 20 条 Red-Blue fixtures 和学习样例。

### 遇到的问题

no-citation case 里，报告没有 evidence，但 Red 仍然追加 omission finding，导致 DELETE 后又 ADD limitation。这说明规则把“没有证据”和“遗漏证据”混在一起了。

### 怎么解决

把 omission 检查收紧成：只有 report.evidence 非空时才检查遗漏。没有 evidence 的强断言应该主要触发 no citation / unsupported，而不是 omission。

### 为什么比 self-reflection 更工程化

Red 和 Blue 输出都有结构化 schema，修复动作可测试、可统计、可复盘。后续 eval 可以计算 repair_precision 和 repair_coverage。

### 怎么验证

- `scripts/inspect_redblue.py --case overclaim`
- `scripts/inspect_redblue.py --case omission --json`
- `tests/unit/test_redblue_cases.py`
- `tests/unit/test_redblue_fixtures.py`

## 7. Evaluation 与正式实验

### 为什么做

只展示几个好看的报告，不足以说明系统稳定。需要离线 benchmark 比较 baseline、verifier、redblue 等配置。

### 做了什么

- ResearchBench-style 主集：35 题。
- Adversarial suite：10 题。
- Red-Blue fixtures：20 条。
- 指标包括 judge mean、Bootstrap 95% CI、Cohen's d、weak_support_rate、atomic_support_rate、repair_precision、repair_coverage。
- `run_eval.py` 支持 config-driven experiments 和 payload integrity check。

### 遇到的问题

指标容易被误读。baseline 不启用 verifier 时 hallucination_rate 看起来为 0，但 weak_support_rate 是 1.0，这说明它没有验证能力，不代表没有幻觉。

### 怎么解决

拆分 hallucination_rate 和 weak_support_rate，并在 `docs/EXPERIMENTS.md` 里明确 result boundary：所有数字只代表 offline/mock benchmark 内部对比。

### 正式结果

ResearchBench run：`20260627_163658`

- 35 题。
- redblue judge mean：0.881。
- redblue hallucination_rate：0.000。
- redblue weak_support_rate：0.490。
- redblue repair_precision：0.886。
- redblue repair_coverage：1.000。

Adversarial run：`20260627_163936`

- 10 题。
- redblue judge mean：0.913。
- redblue hallucination_rate：0.000。
- redblue repair_precision：0.933。
- redblue repair_coverage：1.000。

### 怎么验证

- `scripts/run_eval.py --config configs/default.toml --experiments baseline,memory,compression,verifier,redblue,full`
- `scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue`
- `docs/EXPERIMENTS.md`

## 8. LLM Backend 边界

### 为什么做

简历目标里有多 LLM 后端适配，但项目默认必须离线可复现。真实模型不能破坏测试稳定性。

### 做了什么

- 统一 `LLMBackend` 协议。
- `LLMBackendConfig -> create_llm_backend()`。
- 支持 mock、OpenAI-compatible、DeepSeek、vLLM。
- `inspect_llm_backend.py` 支持 dry-run 和 smoke。
- `run_research.py` 和 `run_showcase.py` 支持传入 backend/model/vLLM base url。
- Showcase Pack 生成 `llm_backend.md`，记录后端配置和 offline safety。

### 遇到的问题

如果真实 LLM 后端进入默认测试，就会受网络、key、成本影响。如果完全不接，又不能说明接口设计。

### 怎么解决

默认 mock，真实后端只做可选 smoke。无 key 时 dry-run 不访问网络；有 key 且显式 `--smoke` 时才调用 completion。

### 怎么验证

- `scripts/inspect_llm_backend.py --backend mock --smoke`
- `scripts/inspect_llm_backend.py --backend deepseek --json`
- `scripts/inspect_llm_backend.py --backend vllm --model local-model --vllm-base-url http://localhost:8000/v1 --json`

## 9. Showcase Pack

### 为什么做

模块越来越多后，单独脚本容易让项目看起来像功能堆叠。需要一个入口证明所有模块接在同一条流水线上。

### 做了什么

新增 `run_showcase.py`，一条命令生成：

- `index.md`
- `plan.md`
- `report.md`
- `report.json`
- `run_summary.json`
- `memory_trace.md`
- `compression_trace.md`
- `verifier_trace.md`
- `redblue_trace.md`
- `eval_summary.md`
- `interview_notes.md`

### 遇到的问题

完整 pipeline 的报告不够适合学习，单个 inspect 脚本又太分散。需要一个“总目录”把所有 trace 串起来。

### 怎么解决

Showcase Pack 使用独立 output directory、memory path、vector path、plan dir，不污染正式实验；同时生成 Markdown/JSON，方便学习和复盘。

### 怎么验证

- `scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？"`
- `tests/integration/test_showcase.py`

## 10. 工程卫生与收尾

### 做了什么

- `.gitignore` 标记 `.venv/`、`.uv-cache/`、`data/memory/*`、`reports/showcase/*`、`reports/experiments/*` 等运行产物。
- `clean_artifacts.py` 支持清理 pycache、egg-info、pytest/ruff cache、memory、plans、reports。
- README、PROJECT_DESIGN、EXPERIMENTS 与最终项目报告对齐到当前实现。
- `check_project_completion.py` 提供最终完成验收入口，检查源码、文档、数据集、showcase 产物和正式实验产物。

### 统一 AgentResult 运行轨迹

后续补强了一个重要细节：Coordinator 不再只是在单测里支持 `BaseAgent.run()`，而是在真实 pipeline 中通过 `_run_agent()` 调用 Planner、Searcher、Reader、Writer、Verifier、Critic 和 BlueRepair。每次调用都会把 `AgentResult` 的 `ok/error/latency/metadata` 写入 SQLite `agent_events`。

这个改动解决的是“接口存在但运行不可观察”的问题。现在学习或排查时，可以从 memory 里看到每个 Agent 对应的阶段、任务或 claim，形成真实的多 Agent 执行轨迹。

### 简历证据追踪

最后补强了 `resume evidence` 机制：每条最终可写进简历的 bullet 都被拆成一张证据卡，包含代码路径、测试、可运行命令、实验产物、学习故事和边界说明。

新增入口：

- `src/deepresearch_agent/resume_evidence.py`
- `scripts/inspect_resume_evidence.py`
- `docs/TRACEABILITY_MATRIX.md`

这个改动解决的是“简历说法和代码证据之间缺少一一映射”的问题。后续复习时，可以先跑：

```powershell
uv run python scripts/inspect_resume_evidence.py --bullet verifier_redblue
```

然后按输出里的源码、测试、命令和产物逐项学习。

## 11. V3 机制补齐

### 做了什么

在 V2 完整链路基础上，补齐更接近目标简历项目的硬机制：

- 状态机新增 `TIMED_OUT`，形成 9 状态任务生命周期。
- Coordinator 增加 timeout/retry、batch lightweight replan、global fallback report 的可观察 trace。
- run summary 增加 `fallback_level`、`replan_count`、`timed_out_tasks`、`batch_failure_events`。
- Red-Blue repair loop 增加 `RepairLoopTrace`，记录每轮 finding、weak claim、repair action、claim fingerprint 和 stop reason。
- Evaluation 增加 `repair_convergence_rate`、`repair_oscillation_rate`、`avg_repair_rounds`。
- ResearchBench 35 题显式标注 `domain`、`required_hops`、`hotpot_style`，支持 per-domain、多跳和 hotpot-style 子集统计。

### 遇到的问题

V2 已经能跑成功路径，但面试官如果追问“失败时怎么办”“Red-Blue 什么时候停”“benchmark 覆盖哪些领域”，原有项目只能回答一部分。

### 怎么解决

没有追求照抄图片里的数字，而是补真实能跑的机制：

- timeout 作为独立状态，而不是普通 failed。
- replan 先做 lightweight recovery task，不引入复杂动态图重写。
- fallback report 明确写 limitations，不伪装证据充分。
- Red-Blue 用 deterministic fingerprint 检测收敛和震荡。
- benchmark 保持 35 题，但显式补 domain 和 HotpotQA-style 标注。

### 怎么验证

新增测试：

- `tests/unit/test_v3_mechanisms.py`
- `tests/unit/test_state_machine.py`
- `tests/integration/test_mock_pipeline.py`

新增学习入口：

```powershell
uv run python scripts/inspect_orchestration_failure.py --case batch_replan
uv run python scripts/inspect_redblue_convergence.py --case oscillation
uv run python scripts/run_eval.py --config configs/default.toml --group-by domain
```

### 最终质量门

```powershell
uv run ruff check src tests scripts
uv run pytest
uv run python -m compileall src scripts tests
uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？"
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue,full
uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue
uv run python scripts/check_project_completion.py
```

最近一次收尾验证：

- ruff passed。
- pytest：94 passed, 3 skipped。
- compileall passed。
- showcase passed。
- ResearchBench eval passed。
- adversarial eval passed。
- completion check passed，包含 67 个路径检查和 88 个文本检查。

## 12. V3 正式实验冻结

### 做了什么

在 V3 机制补齐后，重新跑一轮正式 offline/mock 实验，把新增机制写入稳定产物：

- ResearchBench 主集：35 题，11 个 domain，13 个 multi-hop case，6 个 Hotpot-style case。
- Adversarial suite：10 题，7 个 multi-hop case。
- 指标补齐 `repair_convergence_rate`、`repair_oscillation_rate`、`avg_repair_rounds`、per-domain、multi-hop subset、Hotpot-style subset。
- 更新 README、EXPERIMENTS、FINAL_PROJECT_REPORT 和完成清单到同一组 V3 run id。

### 遇到的问题

正式 ResearchBench 实验中出现过历史 `data/memory/vector_index_redblue.npz` 损坏 warning。这个问题来自旧运行产物，不是源码逻辑错误。

### 怎么解决

没有手动修指标或删除问题，而是让 Coordinator 的 vector index 加载保护生效：损坏 `.npz` 自动重建空索引，并记录 warning 后继续运行。这样可以证明项目对运行产物污染有恢复能力。

### 为什么不使用服务器

本阶段目标是验证离线机制和可复现实验，不需要服务器：

- mock backend、本地 corpus、SQLite、numpy index 和 TextRank 都能本地运行。
- 真实 LLM 会引入网络、费用、随机性，不适合写入正式 offline benchmark。
- 服务器只在未来跑本地 vLLM 或更大模型时需要，当前只保留 backend smoke 入口。

### 当前可引用结果

- ResearchBench run：`20260702_162345_148429_researchbench_21c535de`。
- Adversarial run：`20260702_163315_852511_adversarial_f47f9b96`。
- ResearchBench full：judge mean 0.881，repair_precision 0.886，repair_coverage 1.000。
- Adversarial redblue：judge mean 0.913，repair_precision 0.933，repair_coverage 1.000。
- 这些数字只代表 offline/mock benchmark 内部对比，不能包装成线上效果。

## 13. Resume-Targeted Mechanism Gap Closing

### 做了什么

对照目标简历项目里更硬的工程机制，补齐一轮 V3+ 增强：

- 三层 JSON fallback：strict JSON、fenced/substring JSON、schema repair。
- Red-Blue fixtures 从 20 条扩到 40 条，并补 `failure_mode`、`expected_action`、`expected_status_after_repair`。
- 新增 `run_redblue_eval.py`，输出 repair_success_before、repair_success_after、action_accuracy。
- 新增 orchestration stress cases，覆盖 timeout、retry、batch replan、evidence insufficient 和 global fallback。
- 新增 backend smoke matrix，默认只 smoke mock，真实 OpenAI/DeepSeek/vLLM 在无 key 时 dry-run。
- 新增 Claim Preflight，在 Writer 前做重复 claim、冲突 evidence 和过强断言的轻量处理。

### 当前可引用结果

- Structured JSON fallback：50 条 corrupted-output cases，parse_success_rate 1.000，Level 1/2/3 分布为 6/11/33。
- Red-Blue fixtures：80 条 adversarial fixtures，repair_success_before 0.425，repair_success_after 1.000，action_accuracy 1.000，repair_precision 1.000，repair_coverage 1.000。

### Final Sprint Evidence Pack

**时间：** 2026-07-02

**目标：** 继续对标图片中的 DeepResearch Agent 效果，但坚持所有数字必须来自真实代码和离线实验。

**实现：**

- Red-Blue fixtures 从 40 条扩展到 80 条，新增 `source_of_error`，并在 fixture eval 中输出 repair_precision、repair_coverage、per_failure_mode 和 per_source_of_error。
- Structured JSON fallback cases 从 30 条扩展到 50 条，summary 增加 strict parse success、fallback parse success、schema repair warning count。
- 新增 `run_real_judge_smoke.py`，用于 mock/DeepSeek/OpenAI/vLLM 的 LLM-as-Judge 小样本 smoke；真实 provider 需要显式 `--run-real`，不进入正式 benchmark。
- 新增 `run_final_experiments.py`，将 showcase、eval、Red-Blue、JSON fallback、backend smoke、judge smoke 和 completion check 打包到 `reports/final/<run_id>/`。

**结果：**

- Red-Blue fixtures：80 条，repair_success_before 0.425 -> repair_success_after 1.000。
- Structured JSON fallback：50 条，parse_success_rate 1.000，Level 1/2/3 = 6/11/33。

**边界：**

这些数字来自 deterministic fixtures 和 corrupted-output cases，可以写成“离线样例集上的可复现实验”，不能写成线上真实用户成功率。
- Orchestration stress：6 类固定失败路径。
- Backend smoke matrix：默认 attempted=1，successful=1；真实后端不进入 offline benchmark 指标。

### 边界

这些结果来自固定离线样例，不能写成线上成功率。可以写“在自建 adversarial fixtures 上统计修复前后成功率”，不能写“线上 Red-Blue 成功率提升到 95%”。

## 14. 后续如果继续完善，优先做什么

按优先级：

1. 提升 Verifier：加入更强 contradiction heuristic 或可选 LLM/NLI verifier。
2. 提升 Writer：减少 prohibited claim cue 残留，让 Red-Blue 修复更彻底。
3. 扩大 benchmark：补齐每个 answer_type 至少 7 题。
4. 做真实 LLM 单题 showcase：不混入 offline 指标，只作为 demo。
5. 做 Web/Notebook 展示：基于现有 Markdown/JSON 产物，不重写底层链路。

## 15. 未来学习顺序

等你开始学习时，不要从代码随便翻。按这个顺序：

1. 读 README 和 PROJECT_DESIGN，知道项目全局。
2. 跑 `run_showcase.py`，从 `index.md` 看完整链路。
3. 读本文件，理解每个模块为什么做。
4. 按 `docs/LEARNING_INDEX.md` 一章一章学习。
5. 每学一个模块，就打开对应源码和 tests。
6. 最后读 `docs/FINAL_PROJECT_REPORT.md`，把技术实现串成完整工程故事。
