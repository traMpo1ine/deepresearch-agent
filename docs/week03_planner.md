# Week 03: Planner Agent

本周目标是让 Planner 输出可执行的研究计划，而不是直接回答问题。

核心学习点：

- 复杂问题要拆成背景、实现、风险、评测、权衡等子问题。
- Planner 输出包含 sub_questions、task graph、dependencies、expected_evidence。
- 计划被保存到 `reports/plans/`，方便复盘和博客展示。

当前代码入口：

- `src/deepresearch_agent/agents/planner.py`
