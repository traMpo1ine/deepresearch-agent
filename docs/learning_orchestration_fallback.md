# Orchestration Fallback 学习笔记

## 为什么补这块

原来的 Coordinator 已经支持 DAG、状态机、timeout 和 retry，但失败处理更像“记录错误后继续”。V3 的目标是把失败路径也做成可观察机制：单任务 timeout、批次 replan、全局 fallback report 都要能在 run summary 中看到。

## 现在的机制

- 第 9 个任务状态：`TIMED_OUT`。
- Level 1：任务超过 `timeout_seconds` 后进入 `TIMED_OUT`，还有 retry 机会时回到 `READY`。
- Level 2：同一 batch 出现失败/超时任务时，Coordinator 记录 `batch_failure_events` 并追加 recovery task。
- Level 3：如果 evidence 数量低于 `min_evidence_count`，Writer 仍生成报告，但 limitations 中必须披露 fallback synthesis。

## 可观察字段

`run_summary` 现在包含：

- `fallback_level`
- `replan_count`
- `timed_out_tasks`
- `batch_failure_events`

## 学习命令

```powershell
uv run python scripts/inspect_orchestration_failure.py --case task_timeout
uv run python scripts/inspect_orchestration_failure.py --case batch_replan
uv run python scripts/inspect_orchestration_failure.py --case global_fallback
```

## 面试讲法

我没有只处理成功路径，而是把失败路径也结构化：单任务 timeout 是局部降级，批次失败会触发 lightweight replan，全局证据不足时会强制生成带 limitations 的 fallback report。这样系统即使失败，也能留下可复盘的 trace。

## 边界

当前 replan 是 lightweight recovery task，不是完整动态规划器；它用于展示失败恢复机制，后续可以把 Planner 接入真正的局部重规划策略。
