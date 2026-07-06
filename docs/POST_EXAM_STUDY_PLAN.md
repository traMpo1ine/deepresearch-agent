# 考后 DeepResearch Agent 8 周学习计划

这份计划给考完期末后的你用。现在不用硬学，回来以后按顺序跑、读、改、写。目标不是背代码，而是能讲清楚每个模块为什么存在、怎么实现、如何测试、有什么失败案例。

## Phase 0：期末前低负担维护

- 不做新功能，不开大坑。
- 记住三个入口：`README.md`、`PROJECT_DESIGN.md`、`docs/RESUME_NOTES.md`。
- 记住三条命令：`uv run pytest`、`uv run python scripts/run_research.py "test question"`、`uv run python scripts/run_eval.py --config configs/default.toml`。

## Week 1-2：读懂工程骨架

- 第 1 天：跑通 `uv sync --extra dev`、`uv run pytest`、`run_research.py`、`run_eval.py`。
- 第 2-3 天：读 README 和 PROJECT_DESIGN，运行 `scripts/inspect_plan.py` 观察一个问题如何被拆成 DAG，并画出自己的系统流程图。
- 第 4-5 天：读 DAGTaskGraph、TaskStateMachine、ResearchCoordinator。
- 第 6-7 天：写一篇笔记：`asyncio + Semaphore + DAG 是怎么协作的`。

产出：一张手画流程图、一篇编排学习笔记。

辅助材料：

- `docs/learning_core_schemas.md`
- `docs/learning_orchestration_trace.md`
- `docs/generated/day02_plan.md`

## Week 3-5：逐模块精学

- Week 3：Planner / Searcher / Reader。新增 3 篇 corpus 文档，并确认 Searcher 能召回。
- Week 4：SQLite Memory + numpy Vector Index。增强 `inspect_memory.py` 或写一个 memory debug 笔记。
- Week 5：TextRank + Writer + Citation。给 Markdown report 设计更清楚的 citation trace 展示。

产出：3 个小 PR 级改动、3 篇学习笔记。

## Week 6-7：可信链路

- Week 6：Verifier。构造 5 个 claim-evidence 样例，手动预测状态，再跑测试验证。
- Week 7：Red-Blue + Evaluation。新增 5 条 adversarial fixture，并让测试继续全绿。

产出：Verifier 样例集、Red-Blue fixtures、一次 adversarial eval 记录。

## Week 8：工程增强

优先理解并使用 `EvalIntegrityReport`：

- config snapshot
- dataset summary
- suite source counts
- payload validation status
- experiment memory/vector/plan paths

验收命令：

```powershell
uv run ruff check src tests scripts
uv run pytest
uv run python -m compileall src scripts tests
uv run python scripts/run_eval.py --config configs/default.toml --suite all --experiments baseline,verifier,redblue
```

## 最终目标

8 周后，你应该能不看稿讲清楚：

- 为什么复杂研究任务需要 DAG。
- SQLite 和 numpy vector index 怎么组成共享记忆。
- TextRank 为什么要保护 citation quote。
- Verifier 如何把 claim 拆成 atomic claim 并选择 best evidence。
- Red-Blue 为什么比普通 self-reflection 更工程化。
- ResearchBench、Bootstrap CI、Cohen's d 如何支撑实验叙事。
