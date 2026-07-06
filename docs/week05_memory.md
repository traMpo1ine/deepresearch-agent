# Week 05: SQLite Shared Memory

本周目标是让 Agent 系统拥有跨运行共享记忆。

核心学习点：

- SQLite 存 runs、tasks、evidence、claims、reports、agent_events。
- Memory 不是聊天历史，而是可查询、可审计的结构化运行轨迹。
- 任意 claim 都应该能追溯到 evidence，再追溯到 source chunk。

当前代码入口：

- `src/deepresearch_agent/memory/sqlite_store.py`
- `scripts/inspect_memory.py`

## 怎么观察 SQLite + Vector 的组合

现在可以用固定样例观察“向量召回 id，再回 SQLite 取完整记录”的过程：

```powershell
uv run python scripts/inspect_memory_trace.py --list
uv run python scripts/inspect_memory_trace.py --case sqlite_vector_recall
uv run python scripts/inspect_memory_trace.py --case hybrid_memory_recall --json
uv run python scripts/inspect_memory.py --memory-path reports/showcase/final_check/memory.sqlite3 --schema --runs --limit 5
```

`inspect_memory.py --schema --runs` 用于查看真实 SQLite 文件：

- schema version
- migrations
- table counts
- recent runs
- evidence list

这样可以把“共享记忆”从概念落到可检查的运行产物。

重点看：

- `sqlite_record_count`：SQLite 中保存了多少条可审计 evidence。
- `vector_index_count`：numpy index 中保存了多少个可召回 id。
- `vector_hits[].evidence_id`：向量索引召回的 evidence id。
- `vector_hits[].record`：通过 evidence id 回到 SQLite 后取出的完整 title/source/chunk/quote。

一句话：

```text
Vector index 负责找“可能相关的 id”，SQLite 负责保存“可审计的原始记录”。
```
