# DeepResearch Agent 简历第二项目最终版

目标岗位：AI Agent / RAG / AI 应用开发 / LLM 应用工程日常实习。

GitHub：`https://github.com/traMpo1ine/deepresearch-agent`

## 简历项目标题

**DeepResearch Agent：面向复杂调研任务的可追踪多 Agent 可信生成系统**

独立开发 / 个人项目

技术栈：Python, FastAPI, asyncio, SQLite, numpy, TextRank, DeepSeek API, pytest, GitHub Actions

## 推荐简历 Bullet

- 独立开发 DeepResearch Agent 本地演示系统，基于 FastAPI + 静态前端构建可交互 Web Demo，支持默认 evidence pack 展示、新问题 mock/offline run、状态轮询，以及 Plan DAG、Report、Evidence、Verifier、Red-Blue Repair 全链路可视化。
- 设计 Planner + DAGTaskGraph + TaskStateMachine + Coordinator 多 Agent 编排框架，将复杂调研问题拆解为拓扑依赖任务图，并通过 asyncio + Semaphore 执行同层任务，记录 queued/running/succeeded/failed/blocked/timeout 等任务状态。
- 构建可追踪 RAG 记忆链路，使用 SQLite 结构化保存 runs/tasks/evidence/claims/verification_traces/repair_actions，结合 numpy vector recall、TextRank 引用保护和 Markdown/PDF local corpus profile，实现 claim -> citation -> source chunk -> quote 的证据追溯。
- 实现 atomic Verifier 与 Red-Blue 对抗修复机制，支持 ADD/DELETE/MODIFY/VERIFY repair action、repair loop 收敛/震荡/最大轮数 trace；80 条 adversarial fixtures 上 repair_success 从 0.425 提升到 1.000，repair_precision 达到 1.000。
- 构建 ResearchBench-style 离线评测体系，覆盖 35 题冻结主集、10 题 adversarial suite、60 题 extended ablation 与 80 条 Red-Blue fixtures；60 题 extended benchmark 中 baseline judge mean 0.764 -> full 0.880，weak_support_rate 1.000 -> 0.431，full repair_precision 0.944、repair_coverage 1.000。
- 接入 DeepSeek OpenAI-compatible provider 与 formal LLM verifier benchmark，以 `deepseek-v4-flash` 对 120 个 balanced claim/evidence cases 重复 3 轮共 360 次真实判断，accuracy 0.842、macro-F1 0.831，并将真实 API 输出与 offline/mock benchmark 指标隔离。

## 更短版本

如果简历空间紧张，用下面 4 条：

- 独立开发 DeepResearch Agent，基于 FastAPI + 静态前端构建可演示 Web Demo，支持新问题 mock/offline run，并可视化 Plan DAG、Evidence、Verifier、Red-Blue Repair 全链路。
- 设计 Planner + DAGTaskGraph + TaskStateMachine + Coordinator 多 Agent 编排框架，结合 SQLite 共享记忆、numpy vector recall、TextRank 引用保护和 Markdown/PDF local corpus profile，实现 claim -> citation -> source chunk -> quote 的可追踪 RAG 链路。
- 实现 atomic Verifier 与 Red-Blue 对抗修复，支持 ADD/DELETE/MODIFY/VERIFY action 和 repair loop trace；80 条 adversarial fixtures 上 repair_success 0.425 -> 1.000，repair_precision 1.000。
- 构建 ResearchBench-style 评测体系与 DeepSeek verifier benchmark：60 题 extended ablation 中 baseline judge mean 0.764 -> full 0.880、weak_support_rate 1.000 -> 0.431；360 次 DeepSeek verifier 判断 accuracy 0.842、macro-F1 0.831。

## 一句话介绍

这个项目不是单次 LLM 问答 Demo，而是一个离线可复现的 DeepResearch Agent 工程系统：用户问题先被 Planner 拆成 DAG，多 Agent 执行后把 evidence 写入 SQLite 和向量索引，Writer 基于压缩上下文生成带 citation 的报告，再由 Verifier 和 Red-Blue 模块做 claim 级验证与修复，最后用 ResearchBench-style benchmark 输出可复查指标。

## 3 分钟面试讲稿

我做这个项目的动机是：普通 RAG Demo 通常只展示一次问答结果，但复杂调研任务真正难的是“能不能追踪证据、发现弱支持 claim、修复幻觉，并用指标证明改进”。所以我把系统拆成了规划、执行、记忆、压缩、验证、修复和评测七条链路。

用户问题进入系统后，Planner 会生成 ResearchTask DAG，Coordinator 按拓扑批次并发执行 Searcher 和 Reader。每个 evidence 会写入 SQLite，同时进入 numpy hashing vector index，保证后续 claim 可以回溯到 source chunk 和 quote。Writer 不直接吃全部 evidence，而是先经过 TextRank 压缩，并强制保留 citation quote，避免压缩破坏验证链路。

可信生成部分，我实现了 atomic Verifier，把长 claim 拆成 atomic claims，为每条 claim 选择 best evidence，并记录 verification trace。之后 Red Agent 从事实性、逻辑一致性、引用质量、遗漏信息攻击报告，Blue Agent 只能用 ADD/DELETE/MODIFY/VERIFY 做修复，并记录 repair loop 的收敛、震荡和停止原因。

评测上，我做了 35 题冻结 ResearchBench、10 题 adversarial suite、60 题 extended ablation 和 80 条 Red-Blue fixtures。60 题 extended benchmark 中 baseline judge mean 从 0.764 提升到 full 0.880，weak_support_rate 从 1.000 降到 0.431；80 条 fixtures 上 repair_success 从 0.425 到 1.000。我还用 DeepSeek 做了 360 次 verifier 判断，accuracy 0.842、macro-F1 0.831，但这部分只作为 verifier benchmark，不混入 offline/mock 主指标。

## 8 分钟展开结构

1. 项目动机：从普通 RAG Demo 升级到可追踪、可验证、可修复、可评测的 Agent 系统。
2. 编排链路：Planner -> DAGTaskGraph -> TaskStateMachine -> Coordinator。
3. RAG 链路：Searcher / Reader -> SQLite memory -> numpy vector recall -> citation quote。
4. 可信链路：TextRank compression -> atomic Verifier -> Red-Blue repair loop。
5. 评测链路：ResearchBench-style benchmark、adversarial suite、Bootstrap CI、repair metrics。
6. 工程包装：FastAPI Web Demo、GitHub Actions CI、Demo GIF、traceability matrix。
7. 边界说明：offline/mock 指标不等于线上效果，DeepSeek 真实调用只做 provider/verifier showcase。

## 面试官可能追问

**Q：为什么默认用 mock/offline，而不直接全用真实 LLM？**

A：这个项目优先验证 Agent 工程链路和评测闭环。mock/offline 能保证结果可复现、可回归、成本稳定；真实 DeepSeek 被单独放在 provider smoke 和 verifier benchmark 里，证明 provider 接入与成本边界，但不污染主指标。

**Q：你的 Verifier 是不是严格 NLI？**

A：不是。主链路里的 atomic Verifier 是启发式 claim-evidence 对齐，用来做可解释 trace 和 repair 触发；我额外做了 DeepSeek formal verifier benchmark 作为二级语义判断补强，但仍然不把它包装成生产级 NLI。

**Q：这个项目和普通 RAG 的区别是什么？**

A：普通 RAG 更关注检索和回答，这个项目更强调完整研究链路：任务规划 DAG、证据记忆、引用保护、claim 级验证、Red-Blue 修复和 benchmark 指标。输出不是一段答案，而是一套可追踪报告生成流程。

**Q：本地知识库支持什么？**

A：当前支持 Markdown/TXT/HTML/PDF 资料目录构建 Searcher-compatible JSONL corpus，并在 Web Demo 中通过 corpus profile 切换。它模拟的是企业知识库式 RAG，不做线上上传、多租户权限或全网搜索。

## 投递关键词

AI Agent, Multi-Agent, RAG, DeepResearch, LLM Application, FastAPI, SQLite Memory, Vector Retrieval, TextRank, Verifier, Red-Blue Repair, LLM-as-Judge, DeepSeek, Evaluation, GitHub Actions

## 必须诚实说明的边界

- offline/mock benchmark 是项目内部可复现对比，不代表线上用户场景。
- DeepSeek 真实调用只用于 provider smoke 和 verifier benchmark，不参与主链路指标。
- 当前 vector recall 是 numpy hashing baseline，不是生产级 embedding 服务。
- 当前 Web Demo 是本地作品展示，不是多用户 SaaS。
- 当前本地知识库是资料目录构建，不含权限系统、在线上传或全网搜索。

## 投递前检查

- GitHub 仓库应设为 Public。
- README 顶部应能看到 CI badge、Demo GIF、关键结果和证据入口。
- Actions 页 CI 应至少有一次成功 run。
- 简历链接建议写：`GitHub: github.com/traMpo1ine/deepresearch-agent`
- 若匿名访问 `https://github.com/traMpo1ine/deepresearch-agent` 仍返回 404，重新检查仓库 visibility、owner/repo 拼写和是否需要等待 GitHub 权限生效。
