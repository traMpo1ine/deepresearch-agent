# Week 01: Asyncio Baseline

本周目标是把 DeepResearch Agent 从脚本 demo 变成可调试工程。

核心学习点：

- Python package 结构让 CLI、测试和模块导入保持稳定。
- `asyncio.gather` 负责并发执行同一拓扑层任务。
- `asyncio.Semaphore` 控制最大并发，避免搜索、阅读、模型调用无限展开。
- `AgentResult` 统一记录 Agent 的成功、错误、耗时和元数据。

当前代码入口：

- `src/deepresearch_agent/orchestration/coordinator.py`
- `src/deepresearch_agent/agents/base.py`
- `scripts/run_research.py`

博客主线：

普通 demo 只看最终答案，工程化 Agent 要能回答“谁做了什么、失败在哪里、耗时多少、产物能不能复现”。
