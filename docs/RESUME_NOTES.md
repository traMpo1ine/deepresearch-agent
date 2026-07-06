# 简历与面试素材

本文件用于沉淀最终可写进简历和面试中讲清楚的内容。

## 项目一句话

DeepResearch Agent 是一个面向复杂深度研究任务的多智能体协作系统，覆盖规划、执行、共享记忆、上下文压缩、对抗修复和自动评测。

## 面试讲解顺序

1. 为什么普通 RAG / 单 Agent 不够。
2. 如何用 Planner 将问题拆成 DAG。
3. 如何用 asyncio + Semaphore 控制并发执行。
4. 如何用 SQLite + numpy 做共享记忆和相似检索。
5. 如何用 TextRank 压缩上下文并保护引用。
6. 如何用 Verifier 检查 claim-evidence 对齐。
7. 如何用 Red-Blue 修复幻觉。
8. 如何用 ResearchBench、LLM-as-Judge、Bootstrap CI 评估效果。

## 当前可引用实验结果

以下数字来自 offline/mock benchmark，只能作为本项目内部配置对比，不能写成线上效果：

- Final evidence pack：`reports/final/final_sprint_check/index.md`。
- Final sprint ResearchBench full：judge mean 0.880，95% CI `[0.858, 0.903]`，hallucination_rate 0.000，repair_precision 0.895，repair_coverage 1.000。
- Final sprint adversarial redblue：judge mean 0.920，95% CI `[0.893, 0.950]`，repair_precision 0.883，repair_coverage 1.000。
- V3 ResearchBench 主集：35 题，11 个 domain，13 个 multi-hop case，6 个 Hotpot-style case，run id `20260702_162345_148429_researchbench_21c535de`。
- V3 Adversarial suite：10 题，7 个 multi-hop case，run id `20260702_163315_852511_adversarial_f47f9b96`。
- V3 ResearchBench：full judge mean 0.881，95% CI `[0.859, 0.903]`，hallucination_rate 0.000，weak_support_rate 0.490。
- V3 ResearchBench：full repair_precision 0.886，repair_coverage 1.000，atomic_support_rate 0.619，repair_convergence_rate 1.000，repair_oscillation_rate 0.514。
- V3 Adversarial：redblue judge mean 0.913，95% CI `[0.890, 0.940]`，repair_precision 0.933，repair_coverage 1.000，repair_oscillation_rate 0.300。
- Structured JSON fallback：50 条 corrupted-output cases，parse_success_rate 1.000，Level 1/2/3 分布为 6/11/33。
- Red-Blue fixtures：80 条 adversarial fixtures，repair_success_before 0.425，repair_success_after 1.000，action_accuracy 1.000，repair_precision 1.000，repair_coverage 1.000。
- redblue repair_precision 是简历可引用指标之一，但必须说明来自 offline/mock benchmark 或 fixed fixtures。
- Backend smoke matrix：默认只 smoke mock；OpenAI/DeepSeek/vLLM 无 key 时 dry-run，不进入正式 offline benchmark 指标。
- DeepSeek 真实 API showcase：默认使用 `deepseek-v4-flash`，通过 `scripts/run_deepseek_showcase.py --run-real --max-tokens 512` 生成单题真实调用证据，记录 token usage 和估算成本；不进入正式 offline/mock benchmark 指标。
- Formal LLM Verifier benchmark：`reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/report.md` 在 120 个 balanced claim/evidence cases 上重复 3 轮，共 360 次真实 DeepSeek 判断；accuracy 0.842、macro-F1 0.831、heuristic baseline accuracy 0.467，估算成本 RMB 0.05893803。旧的 LLM Verifier smoke 仍保留为低成本连通性检查。
- Local corpus profiles：`offline_agent_docs`、`resume_agent_docs`、`paper_reading_docs`、`local_kb_docs` 可从本地 Markdown/TXT/HTML/PDF 构建 Searcher-compatible JSONL，Web Demo 可选择 corpus profile，增强本地知识库 RAG 真实感。
- Extended ResearchBench：新增 60 题 `researchbench_extended.jsonl`，五类 answer_type 各 12 题；ablation run `20260705_020934_092414_researchbench_263e905e` 覆盖 baseline / verifier / redblue / full，baseline judge mean 0.764 -> full 0.880，weak_support_rate 1.000 -> 0.431，full repair_precision 0.944，repair_coverage 1.000。
- 典型失败边界：部分 prohibited claim cue 仍会保留，说明 heuristic repair 还不能替代更强 NLI/LLM verifier。

## 当前 v1 可讲内容

- 手写 DAGTaskGraph 和 TaskStateMachine，支持拓扑批次、循环检测、失败阻塞传播。
- 使用 asyncio.gather + Semaphore 执行同层搜索任务，9 状态状态机支持 timeout/retry、失败阻塞和 recovery trace。
- 用 SQLite 保存 runs、tasks、evidence、claims、reports、agent_events，让每个 claim 可以追溯到 evidence/source/chunk/quote。
- 用 numpy hashing vectorizer 实现离线 embedding index，支持相似 evidence 召回和 save/load。
- 用 TextRank 做上下文压缩，同时强制保留 citation quote，避免压缩破坏验证链路。
- 用 Verifier 将长 claim 拆成 atomic claims，为每条 atomic claim 选择 best evidence，并输出 evidence_id、best_quote、overlap score、contradiction cues 和 decision_reason。
- Red Agent 产出 AttackFinding，Blue Agent 执行 ADD/DELETE/MODIFY/VERIFY 并记录 before/after。
- Red-Blue repair loop 记录每轮 finding、weak claim、repair action 和 claim fingerprint，支持收敛/震荡/最大轮数停止理由。
- StructuredOutputParser 支持严格 JSON、fenced/substring JSON、schema repair 三层 fallback，并统计 parse_success_rate。
- Claim Preflight 在 Writer 侧做 claim 去重、冲突提示和过强断言降级。
- 接入 DeepSeek OpenAI-compatible 后端，默认使用低成本 `deepseek-v4-flash`，真实 API 调用需要显式 `--run-real`，并记录 token/cost，避免和离线 benchmark 混写。
- 构建 FastAPI + 静态前端本地 Demo，默认展示 final evidence pack，并支持输入问题启动 mock/offline run、轮询状态和可视化 plan/report/evidence/verifier/redblue 链路。
- 新增 local corpus profile 模式，将本地 Markdown/TXT/HTML/PDF 资料构建为 Searcher-compatible JSONL，并在 Web Demo 中选择不同知识库 profile，展示本地企业知识库式 RAG。
- 新增 formal LLM verifier benchmark，以 claim + evidence + quote 为输入调用 DeepSeek 二级判断，输出 supported/partial/unsupported/contradicted、token usage 和估算成本，并与端到端离线 benchmark 隔离。
- 自建 35题 ResearchBench-style JSONL、10题 adversarial researchbench 和 80条 Red-Blue fixtures，run_eval 输出 judge score、atomic_support_rate、repair_precision、repair_coverage、repair_convergence_rate、Bootstrap 95% CI、Cohen's d。

## 三档面试讲解

### 3 分钟版本

这个项目不是普通 RAG demo，而是一个离线可复现的 DeepResearch Agent。用户问题先由 Planner 拆成 DAG，Coordinator 用 asyncio + Semaphore 执行搜索和阅读任务，Evidence 写入 SQLite 和 numpy 向量索引。Writer 基于 TextRank 压缩后的证据生成带 citation 的报告，Verifier 把长 claim 拆成 atomic claims 并选择 best evidence，Red-Blue 模块再对弱支持 claim 做 DELETE/MODIFY/ADD 修复。最后用 35 题 ResearchBench-style 主集和 10 题 adversarial suite 做 mock/offline 评测，输出 judge score、Bootstrap CI、Cohen's d 和 repair precision/coverage。

### 8 分钟版本

重点讲四条线：

1. 编排线：Planner 产出任务图，DAGTaskGraph 做拓扑批次，TaskStateMachine 管 PENDING/READY/RUNNING/SUCCEEDED/FAILED/BLOCKED。
2. 记忆线：SQLite 保存 runs、tasks、evidence、claims、reports、agent_events、verification_traces、repair_actions；numpy index 做相似 evidence 召回。
3. 可信线：TextRank 压缩保留引用 quote，Verifier 输出多维 trace，Red Agent 从事实性/逻辑/引用/遗漏攻击，Blue Agent 执行 ADD/DELETE/MODIFY/VERIFY。
4. 评测线：run_eval 支持 baseline、verifier、redblue 多配置对比，输出 hallucination_rate、weak_support_rate、citation_coverage、Bootstrap CI、Cohen's d。

### 20 分钟版本

按一次完整运行展开：question -> plan JSON/Mermaid -> DAG execution -> SearchResult lexical/vector/hybrid score -> Reader chunk/quote span -> SQLite trace -> TextRank compressed context -> structured report JSON -> VerificationTrace -> AttackFinding -> RepairAction -> EvaluationResult。讲清楚每个对象为什么要结构化，以及为什么离线优先能避免 API 波动干扰底层系统学习。

## 最终 Bullet v1

- 独立开发 DeepResearch Agent 离线可复现系统，手写 Planner/DAGTaskGraph/TaskStateMachine/Coordinator，将复杂研究问题拆解为多 Agent 任务图，并使用 asyncio + Semaphore 执行拓扑批次任务。
- 设计 9 状态任务状态机与三级降级 trace，区分 timeout、retry、batch replan 和 fallback synthesis，在 run summary 中记录 timed_out_tasks、replan_count 和 fallback_level。
- 构建 SQLite 共享记忆与 numpy hashing vector index，结构化保存 runs/tasks/evidence/claims/verification_traces/repair_actions，实现 claim -> citation -> source chunk -> quote span 的可追溯链路。
- 设计 TextRank 上下文压缩与引用保护机制，通过 L1 向量粗筛、L2 TextRank 句子排序、L3 citation quote 保留，降低上下文长度同时保留可验证证据。
- 实现 Verifier + Red-Blue 对抗修复：Verifier 将长 claim 拆成 atomic claims 并输出多维 VerificationTrace；Blue Agent 执行 ADD/DELETE/MODIFY/VERIFY，并通过 RepairLoopTrace 记录收敛、震荡与最大轮数停止原因。
- 设计三层 JSON fallback 与 Claim Preflight：对 fenced/坏格式/缺字段 JSON 执行结构化解析恢复，并在 Writer 前做重复 claim、冲突 evidence 和过强断言的轻量消解。
- 接入 DeepSeek OpenAI-compatible 后端并新增低成本真实 API showcase，默认使用 `deepseek-v4-flash` 和 `max_tokens` 成本控制，记录 token usage / estimated cost，与 offline/mock benchmark 指标隔离。
- 构建 FastAPI + 静态前端本地 Demo，支持默认 evidence pack 展示、新问题 mock/offline run、状态轮询，以及报告、证据、验证、修复链路可视化。
- 构建 local corpus profile 知识库模式，将 Markdown/PDF 本地资料目录转成可检索 JSONL corpus，并在 Demo 中支持 `offline_agent_docs`、`resume_agent_docs`、`paper_reading_docs`、`local_kb_docs` 场景切换。
- 新增 formal LLM verifier benchmark，以 DeepSeek 对 claim/evidence/quote 做二级 supported/partial/unsupported/contradicted 判断，360 次真实判断 accuracy 0.842、macro-F1 0.831，作为真实 provider 接入和 verifier 补强证据但不进入端到端指标。
- 自建 35 题 ResearchBench-style 离线评测集、10 题 adversarial suite、60 题 extended ResearchBench 和 80 条 Red-Blue fixtures，覆盖 11 个 domain 和 HotpotQA-style 多跳子集；60 题 extended ablation 中 baseline judge mean 0.764 -> full 0.880，weak_support_rate 1.000 -> 0.431，full repair_precision 0.944、repair_coverage 1.000。

## Web Demo 可讲版本

面试演示时我会先打开 `uv run python scripts/run_demo_server.py`，页面默认加载 final evidence pack，让面试官直接看到 Overview、Plan DAG、Report、Evidence & Memory、Verification & Repair 五个区块。然后我输入一个新问题启动 mock/offline run，后端用 FastAPI background task 调用现有 `build_showcase()`，前端轮询状态并展示新生成的 trace。真实 DeepSeek 调用被单独放在 provider smoke 区块，必须显式勾选 real provider，避免把真实 API 输出和 offline benchmark 混写。

## 当前推荐简历第二项目写法

**DeepResearch Agent：面向复杂调研任务的可追踪多 Agent 可信生成系统**

- 独立开发 FastAPI + 静态前端 DeepResearch Demo，支持默认 evidence pack 展示、新问题 mock/offline run、状态轮询，以及 Plan DAG、Report、Evidence、Verifier、Red-Blue Repair 全链路可视化。
- 设计 Planner + DAGTaskGraph + TaskStateMachine + Coordinator 多 Agent 编排框架，结合 SQLite 共享记忆、numpy vector recall 和 TextRank 引用保护，实现 claim -> citation -> source chunk -> quote 的可追踪 RAG 链路。
- 实现 atomic Verifier 与 Red-Blue 对抗修复，支持 ADD/DELETE/MODIFY/VERIFY repair action、repair loop 收敛/震荡/最大轮数 trace；80 条 fixtures 上 repair_success 0.425 -> 1.000、repair_precision 1.000。
- 构建 ResearchBench-style 评测体系：35 题冻结主集 + 10 题 adversarial suite + 60 题 extended ablation，60 题上 baseline judge mean 0.764 -> full 0.880、weak_support_rate 1.000 -> 0.431、full repair_precision 0.944、repair_coverage 1.000。
- 接入 DeepSeek OpenAI-compatible provider smoke 与 formal LLM verifier benchmark，`deepseek-v4-flash` 360 次真实判断 accuracy 0.842、macro-F1 0.831、估算成本 RMB 0.05893803，并与 offline/mock benchmark 指标隔离。

## 3 分钟复试讲稿

老师好，我这个项目叫 DeepResearch Agent，目标不是做一个简单问答 demo，而是复现一个复杂研究任务的多智能体系统。它的核心思路是：用户问题进来后，Planner 先把问题拆成 ResearchTask，并用 DAG 表示依赖；Coordinator 用 asyncio 和 Semaphore 执行同层任务；Searcher 和 Reader 从离线 corpus 里抽取 Evidence；Evidence 同时写入 SQLite 和 numpy vector index，前者负责审计，后者负责相似召回。

生成报告时，我没有让 Writer 直接吃全部 evidence，而是先做 TextRank 压缩，并强制保留 citation quote，避免后面验证时找不到原文。Writer 输出的是结构化 ResearchReport，每个 Claim 绑定 citation ids。之后 Verifier 会把长 claim 拆成 atomic claims，为每个 atomic claim 选择 best evidence，输出 term overlap、quote overlap、missing terms 和 decision reason。最后 Red Agent 从事实性、逻辑一致性、引用质量、遗漏信息攻击报告，Blue Agent 只能执行 ADD、DELETE、MODIFY、VERIFY 这几类动作，并记录 before/after。

我还做了评测体系：35 题 ResearchBench-style 主集、10 题 adversarial suite、60 题 extended ResearchBench 和 80 条 Red-Blue fixtures。最终 evidence pack 里，ResearchBench full 配置的 judge mean 是 0.880，repair_precision 是 0.895，repair_coverage 是 1.000；60 题 extended ablation 里 baseline judge mean 0.764 提升到 full 0.880，weak_support_rate 从 1.000 降到 0.431；固定 Red-Blue fixtures 上 repair_success 从 0.425 提升到 1.000。我还接了 DeepSeek OpenAI-compatible 后端，用 `deepseek-v4-flash` 做低成本真实 API showcase 和 formal verifier benchmark，360 次真实判断 accuracy 0.842、macro-F1 0.831，但这些真实输出不会混入离线 benchmark。这个项目对我最大的训练是，我把 Agent 系统拆成了可追踪、可验证、可修复、可评测的工程链路，而不是只追求一次生成结果。

## Bullet 对应代码

- DAG/并发：`src/deepresearch_agent/orchestration/`
- 记忆/检索：`src/deepresearch_agent/memory/`
- 压缩：`src/deepresearch_agent/compression/textrank.py`
- 验证/修复：`src/deepresearch_agent/agents/verifier.py`、`src/deepresearch_agent/redblue/`
- 评测：`src/deepresearch_agent/evaluation/`、`scripts/run_eval.py`

更完整的逐条证据映射见：

- `docs/TRACEABILITY_MATRIX.md`
- `uv run python scripts/inspect_resume_evidence.py --bullet verifier_redblue`

原则：以后简历里每新增一句技术描述，都要先补一条 resume evidence，包含代码路径、测试、命令、产物和边界，避免写出无法被项目支撑的说法。
