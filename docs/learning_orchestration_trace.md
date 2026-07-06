# Orchestration Trace 学习笔记

这份文档解释一次 DeepResearch run 是怎么从问题走到报告的。

## 1. Planner 生成任务

用户输入一个问题后，`PlannerAgent` 不直接回答，而是生成 `ResearchPlan`：

```text
root
  -> search background
  -> search implementation
  -> search reliability risk
  -> search evaluation metric
  -> search tradeoffs
  -> synthesize
  -> verify
  -> repair
```

可以用下面命令只观察任务图：

```powershell
uv run python scripts/inspect_plan.py "为什么 DeepResearch Agent 需要引用验证？"
```

## 2. DAG 生成拓扑批次

`DAGTaskGraph` 根据 `dependencies` 计算哪些任务能同时执行。当前默认 Heuristic Planner 会根据问题类型改变依赖，因此不同问题的批次数可能不同。

Template Planner 的典型批次是：

```text
Batch 1: root
Batch 2: five search tasks
Batch 3: synthesize
Batch 4: verify
Batch 5: repair
```

Batch 2 可以并发，因为五个 search 任务都只依赖 root，互相之间没有依赖。

## 3. Coordinator 执行任务

`ResearchCoordinator` 是总调度：

- 调用 Planner 得到 plan。
- 用 DAGTaskGraph 得到执行批次。
- 用 TaskStateMachine 更新任务状态。
- 用 asyncio + Semaphore 并发执行同一批任务。
- 调用 Searcher / Reader 生成 Evidence。
- 调用 Writer 生成 ResearchReport。
- 调用 Verifier / Red-Blue 检查并修复 Claim。
- 把任务、证据、claim、报告和修复动作写入 SQLite。

## 4. Memory 保存结果

SQLite 记录一次运行的可追溯链路：

```text
runs -> tasks -> evidence -> claims -> verification_traces -> repair_actions -> reports
```

这条链路让系统能回答：

- 这个报告来自哪次 run？
- 每个任务是否成功？
- 每条 claim 引用了哪些 evidence？
- Verifier 为什么判定它 supported / partial / unsupported？
- Blue Agent 做过哪些修复？

## 5. 今天先掌握的一句话

DeepResearch 的核心不是一次生成答案，而是把研究过程拆成可观察、可追踪、可评测的任务链路。
