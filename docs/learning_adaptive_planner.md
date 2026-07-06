# Adaptive Planner 学习笔记

## 为什么优化 Planner

旧版 Planner 对任何问题都生成固定五类子任务：背景、实现、风险、评测、权衡。它稳定、可复现，适合作为 baseline，但不同问题得到的 DAG 几乎相同。

当前项目保留两种模式：

- `template`：固定模板，作为实验 baseline。
- `heuristic`：根据问题关键词识别问题类型，并生成不同子任务和依赖。

## PlanType

Heuristic Planner 当前支持四类计划：

- `comparison`：对比、区别、优缺点、versus。
- `risk_analysis`：风险、故障、幻觉、可靠性、引用验证。
- `solution_design`：如何实现、架构、方案设计。
- `general`：没有命中特定类型时使用通用模板。

## 不同问题如何产生不同 DAG

比较问题：

```text
定义比较范围与指标
  +-> 收集方案 A 证据
  +-> 收集方案 B 证据
         -> 跨方案比较与适用场景
         -> synthesize -> verify -> repair
```

风险问题：

```text
背景 + 失败模式
         -> 缓解机制
         -> 评测标准 + 残余局限
         -> synthesize -> verify -> repair
```

因此比较问题和风险问题不只子问题文本不同，任务数量、依赖边和拓扑批次也会不同。

## 如何观察

```powershell
uv run python scripts/inspect_plan.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
uv run python scripts/inspect_plan.py "为什么 DeepResearch 需要引用验证？" --planner-mode heuristic
uv run python scripts/inspect_plan.py "比较 SQLite 和向量数据库的优缺点" --planner-mode template
```

当前默认模式是 `heuristic`，可以在 `configs/default.toml` 的 `pipeline.planner_mode` 中修改。

## 当前边界

Heuristic Planner 仍然是规则系统，不理解复杂语义。它的价值是：

- 比固定模板更问题自适应。
- 离线可复现，便于测试。
- 为未来 LLMPlanner 提供明确 baseline。

后续可以比较 `template vs heuristic vs llm`，而不是直接用真实模型替换所有逻辑。
