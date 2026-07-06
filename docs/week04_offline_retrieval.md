# Week 04: Offline Retrieval and Reader

本周目标是建立离线可复现的搜索和阅读链路。

核心学习点：

- 本地 corpus 避免网络和 API 不稳定。
- Searcher 使用 TF-IDF-lite 排序。
- Reader 做 chunking、quote extraction、source metadata。
- Evidence 必须能反查 source、chunk 和 quote。

当前代码入口：

- `data/corpus/offline_corpus.jsonl`
- `src/deepresearch_agent/agents/searcher.py`
- `src/deepresearch_agent/agents/reader.py`
