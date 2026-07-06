# DeepResearch Agent Learning Index

这是一条复习路线。不要从所有源码开始读，按“故事 -> 命令 -> 输出 -> 源码”的顺序学。

## 0. 先建立全局故事

读：

- `README.md`
- `PROJECT_DESIGN.md`
- `docs/PROJECT_COMPLETION_LOG.md`
- `docs/FINAL_COMPLETION_CHECKLIST.md`
- `docs/FINAL_PROJECT_REPORT.md`
- `docs/BUILD_LOG.md`

要能讲出一句话：

```text
DeepResearch Agent 不是直接生成答案，而是把研究任务拆成可观察、可追踪、可验证、可修复、可评测的工程流水线。
```

先跑一条完整展示链路：

```powershell
uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？"
```

看输出目录：

- `index.md`：总入口。
- `plan.md`：Planner 和 DAG。
- `report.md` / `report.json`：最终报告。
- `memory_trace.md`：SQLite + vector recall。
- `compression_trace.md`：TextRank 压缩和 quote preservation。
- `verifier_trace.md`：atomic claim verification。
- `redblue_trace.md`：Red finding 和 Blue repair action。
- `eval_summary.md`：离线评测指标示例。
- `interview_notes.md`：把一次运行讲成 60 秒故事。

## 1. Core Schemas

读：

- `docs/learning_core_schemas.md`
- `src/deepresearch_agent/schemas/core.py`

重点对象：

- `ResearchTask`
- `ResearchPlan`
- `Evidence`
- `Claim`
- `VerificationTrace`
- `RepairAction`

要能讲：为什么所有中间结果都要结构化，而不是到处传字符串。

## 2. Planner 与 DAG

跑：

```powershell
uv run python scripts/inspect_plan.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
uv run python scripts/inspect_plan.py "为什么 DeepResearch Agent 需要引用验证？" --planner-mode heuristic
```

读：

- `docs/learning_adaptive_planner.md`
- `docs/learning_orchestration_trace.md`
- `docs/generated/day02_plan.md`

看输出：

- `plan type`
- `tasks`
- `dependencies`
- `topological batches`
- Mermaid DAG

要能讲：Planner 决定研究路线，DAG 决定执行顺序和并发边界。

## 3. Searcher Grounding

跑：

```powershell
uv run python scripts/run_research.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
```

读：

- `docs/learning_searcher_grounding.md`
- `src/deepresearch_agent/agents/searcher.py`
- `data/corpus/offline_corpus.jsonl`

看输出：

- Evidence 是否命中 SQLite/vector/hybrid memory。
- Key claims 是否有 citations。
- Verifier 是否判为 supported。

要能讲：Planner 拆得对还不够，Searcher 找准证据后 Writer 和 Verifier 才能闭环。

## 4. SQLite Memory + Numpy Vector Index

跑：

```powershell
uv run python scripts/inspect_memory_trace.py --list
uv run python scripts/inspect_memory_trace.py --case sqlite_vector_recall
uv run python scripts/inspect_memory_trace.py --case hybrid_memory_recall --json
```

读：

- `docs/week05_memory.md`
- `docs/week06_vector_retrieval.md`
- `docs/generated/day06_memory_trace.md`
- `src/deepresearch_agent/memory/sqlite_store.py`
- `src/deepresearch_agent/memory/vector_index.py`

看输出：

- SQLite records
- Vector index items
- vector hits
- SQLite record returned by evidence id
- quote/source/chunk

要能讲：vector index 负责相似召回，SQLite 负责保存可审计原文记录。

## 5. TextRank Compression

跑：

```powershell
uv run python scripts/inspect_compression.py --list
uv run python scripts/inspect_compression.py --case quote_preservation
uv run python scripts/inspect_compression.py --case multi_quote_preservation --json
```

读：

- `docs/week07_textrank_compression.md`
- `docs/generated/day05_compression_trace.md`
- `src/deepresearch_agent/compression/textrank.py`

看输出：

- original char count
- compressed char count
- compression ratio
- preserved quote count
- selected sentences

要能讲：上下文压缩不是普通摘要，核心是压缩时不破坏 citation quote 和后续验证链路。

## 6. Verifier Atomic Claims

跑：

```powershell
uv run python scripts/inspect_verification.py --list
uv run python scripts/inspect_verification.py --case mixed_atomic
uv run python scripts/inspect_report_trace.py --report-json reports/showcase/final_check/report.json
```

读：

- `docs/learning_verifier_atomic_claims.md`
- `docs/generated/day03_verifier_trace.md`
- `src/deepresearch_agent/agents/verifier.py`

看输出：

- atomic claims
- best evidence
- term overlap
- quote overlap
- missing terms
- decision reason
- report claim -> citation -> evidence -> repair action

要能讲：atomic verification 解决的是“长 claim 里一部分对、一部分错”的问题。

## 7. Red-Blue Repair

跑：

```powershell
uv run python scripts/inspect_redblue.py --list
uv run python scripts/inspect_redblue.py --case overclaim
uv run python scripts/inspect_redblue.py --case omission --json
```

读：

- `docs/learning_redblue_fixtures.md`
- `docs/generated/day04_redblue_trace.md`
- `src/deepresearch_agent/agents/critic.py`
- `src/deepresearch_agent/redblue/blue_agent.py`

看输出：

- Red finding 的 category/severity/reason。
- Blue action 的 ADD/DELETE/MODIFY/VERIFY。
- before/after。
- limitation 是否被添加。

要能讲：Red-Blue 把“反思”变成结构化、可测试、可审计的修复动作。

## 8. Evaluation

跑：

```powershell
uv run python scripts/inspect_eval_metrics.py --case baseline_vs_redblue
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue
```

读：

- `docs/learning_evaluation_metrics.md`
- `docs/generated/day07_eval_metrics_trace.md`
- `docs/EXPERIMENTS.md`
- `src/deepresearch_agent/evaluation/runner.py`

看输出：

- judge score
- weak support rate
- atomic support rate
- repair precision / coverage
- Bootstrap 95% CI
- Cohen's d

要能讲：评测不是挑几个好例子，而是用同一离线 benchmark 比较不同 pipeline config。

## 9. Config + LLM Backend

跑：

```powershell
uv run python scripts/inspect_llm_backend.py --backend mock --smoke
uv run python scripts/inspect_llm_backend.py --backend deepseek --json
uv run python scripts/inspect_llm_backend.py --backend vllm --model local-model --vllm-base-url http://localhost:8000/v1 --json
```

读：

- `docs/learning_config_backend.md`
- `docs/generated/day08_llm_backend_trace.md`
- `src/deepresearch_agent/llm/factory.py`
- `src/deepresearch_agent/llm/openai_compatible.py`

看输出：

- backend
- model
- base_url
- env_var
- env_configured
- offline_safe

要能讲：真实 LLM 后端是可选增强，默认 mock 保证离线可复现。

## 10. 最后整理表达

读：

- `docs/INTERVIEW_QA.md`
- `docs/RESUME_NOTES.md`

练习顺序：

1. 先讲系统整体故事。
2. 再讲一次真实问题怎么被发现和修复。
3. 最后讲指标边界：这是 offline/mock benchmark，不夸大成线上效果。
