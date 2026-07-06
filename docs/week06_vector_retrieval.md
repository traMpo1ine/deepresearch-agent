# Week 06: Numpy Vector Retrieval

本周目标是用 numpy 实现轻量 embedding 相似检索。

核心学习点：

- hashing vectorizer 可以作为离线可复现 embedding。
- cosine similarity 用矩阵乘法即可实现。
- vector index 只保存召回能力，原文仍保存在 SQLite。

当前代码入口：

- `src/deepresearch_agent/memory/vector_index.py`

## 为什么不直接把原文存在向量索引里

向量索引适合做相似召回，但不适合作为唯一事实来源。它返回的是相似 id 和分数，不适合保存完整审计链路。

当前设计是：

```text
NumpyVectorIndex.search(query) -> evidence ids
SQLiteMemoryStore.get_evidence(id) -> title / source_id / chunk_id / quote / metadata
```

这样既能复用历史 evidence，又能保留 claim -> citation -> source chunk -> quote 的追溯路径。

观察命令：

```powershell
uv run python scripts/inspect_memory_trace.py --case hybrid_memory_recall --json
```
