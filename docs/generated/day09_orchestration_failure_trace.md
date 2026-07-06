# Day 09 Orchestration Failure Trace

固定观察命令：

```powershell
uv run python scripts/inspect_orchestration_failure.py --case batch_replan
```

核心输出：

- `fallback_level = 2`
- `replan_count = 1`
- batch 中失败任务会被记录到 `batch_failure_events`
- recovery task 不重写整个 DAG，只补偿失败任务的 evidence 路径

学习重点：

1. `TIMED_OUT` 是第 9 个任务状态，用于区分 timeout 和普通失败。
2. Level 1 处理单任务 timeout/retry。
3. Level 2 记录 batch failure，并触发 lightweight replan。
4. Level 3 在 evidence 不足时生成带 limitations 的 fallback report。

这条 trace 的意义：失败路径也必须可观察，不能只在成功样例里展示 Agent 系统。
