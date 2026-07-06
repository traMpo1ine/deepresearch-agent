# 从 RAG Demo 到 DeepResearch Agent：可追踪、可验证、可修复的多 Agent 系统

很多 RAG Demo 的终点是“给一个问题，返回一段答案”。这个项目刻意把终点往后推了一步：答案生成以后，还要能回答三个问题：

1. 每个 claim 来自哪条 evidence、哪个 chunk、哪段 quote？
2. 哪些 claim 是 supported、partial、unsupported 或 contradicted？
3. 当发现弱引用或幻觉时，系统如何记录 repair action，而不是只静默改写？

## 1. 为什么不只做单 Agent RAG

单 Agent 问答适合快速验证 prompt，但复杂调研任务通常包含背景梳理、证据检索、对比分析、风险判断和结论生成。把所有步骤塞进一个 prompt，最大的问题不是“不能生成”，而是生成之后很难调试。

DeepResearch Agent 的第一层是 Planner + DAGTaskGraph：Planner 把问题拆成 ResearchTask，DAG 记录依赖关系，Coordinator 按拓扑批次执行。这样每个子任务都有状态、输入、输出和失败原因。

## 2. 共享记忆：让证据留下来

系统把 runs、tasks、evidence、claims、agent events 和 repair actions 写入 SQLite。SQLite 的价值不是炫技，而是让一次运行结束后仍能追问：

- 这个 claim 引用了哪些 evidence ids？
- evidence 的 source、chunk、quote 是什么？
- Verifier 为什么把它判成 partial？
- Blue Agent 做了 ADD、DELETE、MODIFY 还是 VERIFY？

同时，项目用 numpy hashing vector index 做轻量相似召回。它不是生产级向量数据库，但足够支撑离线可复现的 baseline，并且接口未来可以替换为真实 embedding 或 FAISS/Chroma。

## 3. 压缩不能破坏引用

长上下文压缩如果只追求更短，很容易把证据 quote 删掉。这个项目的 TextRank 压缩会选择高相关句子，同时保留 citation quote，使 Writer 和 Verifier 仍能共享同一条证据链。

这也是项目和普通摘要脚本的区别：压缩不是为了让输出更短，而是为了让后续验证仍有证据可查。

## 4. Verifier 与 Red-Blue Repair

Verifier 会把长 claim 拆成 atomic claims，并对每条 atomic claim 计算 term overlap、quote overlap、contradiction cues 和 best evidence。输出不是一个模糊分数，而是 VerificationTrace。

Red-Blue 修复在 Verifier 之后运行：

- Red Agent 从事实性、逻辑、引用、遗漏角度攻击报告。
- Blue Agent 只能执行 ADD、DELETE、MODIFY、VERIFY。
- RepairLoopTrace 记录每轮是否收敛、是否震荡、是否达到最大轮数。

这让“修复幻觉”从一句口号变成了可审计的数据结构。

## 5. 从离线稳定到真实 provider

正式 benchmark 默认使用 offline/mock，是为了保证每次评测可复现，不受 API 波动影响。真实 DeepSeek 接入被放在 provider smoke 和 LLM verifier smoke 中：

- 默认 dry-run，不扣费。
- 显式 `--run-real` 才调用真实 API。
- 记录 prompt tokens、completion tokens、total tokens 和 estimated cost。
- 不把真实 API 输出混入 offline/mock benchmark 指标。

这个边界很重要：作品可以证明自己接得上真实模型，但指标必须保持可复现。

## 6. 本地知识库 RAG 模式

为了让项目更像 AI 应用场景，而不是纯离线玩具，新增了 local corpus profile：

- `offline_agent_docs`：项目机制说明。
- `resume_agent_docs`：简历和面试讲解资料。
- `paper_reading_docs`：论文阅读/文献调研场景。

资料以 Markdown/TXT/HTML 存放，脚本会构建 Searcher-compatible JSONL。Web Demo 可以选择 corpus profile，启动一次新的 mock/offline run，并展示 plan、report、evidence、memory、verification 和 repair。

## 7. 评测与简历表达

当前可以引用的正式数字来自冻结 evidence pack：35 题 ResearchBench-style 主集、10 题 adversarial suite、80 条 Red-Blue fixtures。新增的 60 题 extended ResearchBench 用于下一轮扩容评测，不能在未重跑前写成正式效果。

适合写进简历的不是“我做了 RAG”，而是：

- 多 Agent DAG 编排。
- SQLite + vector recall 的可追踪记忆。
- claim-level citation 与 atomic verification。
- Red-Blue repair loop。
- offline/mock benchmark 与真实 provider smoke 的边界管理。
- FastAPI Web Demo 可现场演示。

## 8. 项目边界

这个项目仍然是本地作品展示，不是线上多用户产品。当前 verifier 是 heuristic，不是严格 NLI；local corpus profile 不是全网搜索；extended benchmark 需要重跑后才能产出正式指标。

但它已经具备一个 AI Agent / AI 应用实习作品最重要的骨架：能运行、能解释、能追踪、能评测，也知道哪些地方不能夸大。
