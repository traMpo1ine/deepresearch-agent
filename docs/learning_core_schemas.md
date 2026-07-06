# Core Schemas 学习笔记

这份文档解释 `src/deepresearch_agent/schemas/core.py` 里的核心数据结构。源码里只保留简洁 docstring，详细解释放在这里。

## 为什么先看 Schema

DeepResearch Agent 的每个模块都围绕结构化对象协作。先理解这些对象，比直接读 Coordinator 更容易建立地图：

- `ResearchTask`：任务图里的一个节点。
- `ResearchPlan`：Planner 输出的一整张任务图。
- `Evidence`：Searcher/Reader 找到的可追溯证据。
- `Claim`：Writer 写出的报告结论。
- `VerificationTrace`：Verifier 判断 claim 是否被 evidence 支持的过程记录。
- `RepairAction`：Blue Agent 对弱结论做出的修复动作。
- `EvaluationResult`：评测脚本输出的一条结果。

## AgentResult

`AgentResult` 是每个 Agent 的统一输出包装，字段包括：

- `agent_name`
- `ok`
- `output`
- `error`
- `latency_seconds`
- `metadata`

所有 Agent 都可以通过统一入口调用：

```python
result = await agent.run(agent_input, context=None)
```

这个入口会返回 `AgentResult`，并把异常包装成 `ok=False`，避免调用方只能靠 try/except 才知道哪个 Agent 失败。

各 Agent 仍然保留专用方法：

- `PlannerAgent.plan(question)`
- `SearcherAgent.search(task)`
- `ReaderAgent.read(task, results)`
- `WriterAgent.write(question, evidence, context, plan_type)`
- `VerifierAgent.verify(claim, evidence)`
- `CriticAgent.review(report)`
- `BlueRepairAgent.repair(report, findings)`

统一 `run()` 用于框架编排和可观察性；专用方法用于模块内部清晰表达。

## ResearchTask

`ResearchTask` 可以理解成一张任务卡：

- `question`：这个任务要解决的具体问题。
- `id`：任务唯一编号，其他任务通过它声明依赖。
- `task_type`：任务类型，例如 root、search、synthesize、verify、repair。
- `parent_id`：这个任务由哪个上级任务拆出来。
- `dependencies`：必须先完成哪些任务。
- `status`：当前生命周期状态，例如 pending、running、succeeded、blocked。
- `retry_count` / `max_retries`：失败重试信息。
- `timeout_seconds`：任务执行超时时间。
- `error`：失败原因。

最重要的是 `dependencies`。它让系统知道哪些任务可以并发，哪些任务必须等待。

## ResearchPlan

`ResearchPlan` 是 Planner 的输出。它包含：

- 用户原始问题 `root_question`。
- 一组 `ResearchTask`。
- 拆解理由 `rationale`。
- 子问题列表 `sub_questions`。
- 规划质量检查 `quality_report`。

`ResearchPlan` 可以直接交给 `DAGTaskGraph`，变成可执行的任务依赖图。

## Evidence 和 Claim

`Evidence` 是证据，记录来源、原文、quote、chunk、score 等信息。

`Claim` 是报告中的结论。每个 Claim 应该绑定 citation ids，也就是指向 Evidence 的 id。

这两个对象共同保证：

```text
报告结论 -> citation id -> evidence -> source/chunk/quote
```

## VerificationTrace

`VerificationTrace` 是 Verifier 的审计记录。它解释：

- claim 命中了哪些 evidence。
- 哪些关键词被支持。
- 哪些关键词缺失。
- 是否存在 contradiction cues。
- atomic claim 的逐条判断结果。

这让“幻觉检测”不是一句空话，而是可以追踪到具体证据。

## RepairAction

`RepairAction` 记录 Red-Blue 修复动作：

- `ADD`：补充 limitation 或谨慎 claim。
- `DELETE`：删除 unsupported / contradicted claim。
- `MODIFY`：把强断言改成更谨慎的表达。
- `VERIFY`：确认已支持 claim，不改正文。

每个动作保留 before/after，方便评测和复盘。

## EvaluationResult

`EvaluationResult` 是评测输出，包含：

- factual accuracy
- hallucination rate
- weak support rate
- citation coverage
- atomic support rate
- repair precision / coverage
- judge score
- bootstrap CI
- Cohen's d

它是后续实验报告和技术博客的基础。
