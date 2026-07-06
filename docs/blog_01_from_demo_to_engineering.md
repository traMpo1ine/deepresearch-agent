# 从 Demo 到 DeepResearch Agent 工程

核心观点：一个能写进简历的 Agent 项目不能只展示最终回答，而要展示可观测的规划、执行、记忆、验证、修复和评测链路。

普通 RAG demo 的问题是，它很容易把所有复杂性藏在一次模型调用里。用户只看到一个答案，但看不到问题如何拆解、证据从哪里来、哪些结论缺少支持、失败时系统如何恢复。面试时如果只能展示一个漂亮输出，很难讲出工程深度。

DeepResearch Agent 的设计目标正好相反：把最终答案拆成一条可以审计的数据流。Planner 先把问题拆成子任务，DAGTaskGraph 管理依赖，Coordinator 用 asyncio 和 Semaphore 执行同层任务，Searcher/Reader 产生 evidence，Writer 生成 claim，Verifier 检查 claim-evidence 对齐，Red-Blue 再做对抗修复。每一步都写入 SQLite 或 JSON 报告。

这个项目故意选择离线优先。mock LLM、本地 corpus、ResearchBench-style 数据集让实验可复现，避免早期被网络、API 成本和模型随机性拖住。真实 LLM 后端保留为可选增强，而不是默认依赖。

最终评价一个 Agent 项目，不是看它是否“看起来聪明”，而是看它能否回答这些问题：它为什么这么计划？证据在哪里？哪些 claim 是弱支持？修复动作有没有 before/after？评测结果能不能复现？这就是从 demo 到工程的分界线。
