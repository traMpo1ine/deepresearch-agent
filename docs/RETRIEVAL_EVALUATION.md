# Searcher 检索质量评测

## 为什么单独评测检索

端到端报告分数会混合 Planner、Reader、Writer、Verifier 和 mock judge 的影响。即使最终报告看起来正确，也不能说明 Searcher 找到了正确证据。因此本项目把检索作为独立组件评测，并把漏召案例直接保留下来。

## 数据与冻结方式

- 查询：`data/benchmarks/researchbench.jsonl` 的 35 个问题。
- relevance label：每题人工维护的 `required_sources`，一题可以有 1–3 个相关文档。
- corpus：`data/corpus/offline_corpus.jsonl`，共 23 个可提交的项目知识文档。
- 联网搜索：关闭；本实验只测本地检索，不把网络波动混入排序指标。
- 私人数据：不包含用户论文正文，也不包含上传目录。
- 可追溯性：报告记录 benchmark 与 corpus 的 SHA-256；运行前验证每个 relevance id 都真实存在。

这里“冻结”指固定文件与 hash 的可复现回归集，不代表独立第三方盲测。该数据也参与过项目开发和权重校准，所以指标不能外推为生产准确率。

## 三种消融模式

| 模式 | 排序信号 | 用途 |
|---|---|---|
| lexical | 简化 TF-IDF | 精确术语基线 |
| vector | 64 维 hashing vector cosine | 无 API、确定性的教学向量基线 |
| hybrid | `lexical + 0.20 * vector + topic` | 当前默认检索器 |

`trust_level` 只做同分 tie-break，不进入相关性加法。首轮基线曾把 trust 直接加分，导致高可信但无关的 SQLite/vector 文档挤进 Top‑5；正式评测发现后修正了这一语义错误。向量权重从 0.35 降到 0.20，是因为 64 维 hashing 会发生碰撞，过高权重使 hybrid Recall@5 从 0.843 降到 0.814。

## 指标

- Recall@K：Top‑K 找回的 relevance labels 占全部 labels 的比例；多跳题尤其重要。
- Hit@K：Top‑K 是否至少命中一个相关文档。
- All-relevant@K：Top‑K 是否找齐所有相关文档，直接暴露多跳证据缺失。
- MRR@K：第一个相关文档排名的倒数均值，衡量首个正确证据是否靠前。
- nDCG@K：考虑多个相关文档及其排名折损。

## 冻结结果

报告：`reports/retrieval_eval/benchmark_v3/report.md`

| Mode | Recall@1 | Recall@3 | Recall@5 | Hit@5 | All relevant@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.633 | 0.786 | 0.843 | 0.943 | 0.743 | 0.843 | 0.796 |
| vector | 0.229 | 0.529 | 0.610 | 0.686 | 0.543 | 0.432 | 0.457 |
| hybrid | 0.662 | 0.786 | 0.843 | 0.943 | 0.743 | 0.852 | 0.804 |

结论不是“向量一定更好”。当前 hashing vector 单独表现明显较弱；hybrid 保持 lexical 的 Recall@5，并把 MRR@5 从 0.843 提到 0.852。35 题中仍有 9 题至少漏掉一个 label，尤其集中在 citation verification 和 2–3 hop 查询。

真实百炼 `text-embedding-v4` 使用相同数据与hash复跑：

| Mode | Recall@1 | Recall@3 | Recall@5 | Hit@5 | All relevant@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.633 | 0.786 | 0.843 | 0.943 | 0.743 | 0.843 | 0.796 |
| real vector | 0.690 | 0.886 | 0.943 | 1.000 | 0.886 | 0.910 | 0.890 |
| real hybrid | 0.662 | 0.810 | 0.867 | 0.943 | 0.771 | 0.852 | 0.822 |

真实vector在15题上提高Recall@5且没有题目退化，说明dense语义信号有效；但固定`lexical + 0.20 * vector + topic`融合仍由词法分数主导，只将hybrid Recall@5提高到0.867。后续调整融合权重必须使用独立开发集，不能在同一35题上反复调参后继续称其为盲测结果。

## 80 条冻结 held-out v1

`data/benchmarks/retrieval_holdout_v1.jsonl` 是与上述35题分开编写的一次性冻结集，共80条：

- 47条中文、33条英文；
- 40条单跳，40条2–5跳；
- 覆盖 paraphrase、scenario、negative、contrast、colloquial、long query 等10类查询风格；
- relevance labels仍指向相同23文档 corpus，但问题未参与原权重和 query expansion 开发；
- v1不进入CI、不允许据此修改检索权重；公开后也不再把它复用为下一轮“盲测”。

首跑结果：

| Mode | Recall@1 | Recall@3 | Recall@5 | Hit@5 | All relevant@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| lexical | 0.315 | 0.573 | 0.666 | 0.738 | 0.588 | 0.585 | 0.573 |
| hashing vector | 0.058 | 0.225 | 0.371 | 0.500 | 0.225 | 0.239 | 0.246 |
| hashing hybrid | 0.290 | 0.532 | 0.644 | 0.713 | 0.562 | 0.549 | 0.543 |
| real vector | 0.606 | 0.866 | 0.920 | 0.988 | 0.838 | 0.915 | 0.878 |
| real hybrid | 0.465 | 0.786 | 0.860 | 0.925 | 0.788 | 0.783 | 0.772 |

最关键的发现不是单一总分，而是泛化差距：hashing hybrid中文Recall@5只有0.468，真实vector中文Recall@5达到0.925。另一方面，真实vector仍优于固定融合的real hybrid，说明后续应在新的开发集上研究RRF或动态融合，不能回头用held-out v1调权重。

报告：

- `reports/retrieval_eval/holdout_v1_hashing/report.md`
- `reports/retrieval_eval/holdout_v1_dashscope/report.md`

## 运行与回归门禁

```powershell
uv run python scripts/run_retrieval_eval.py `
  --output-dir reports/retrieval_eval/latest `
  --min-hybrid-recall-at-max-k 0.84
```

输出包括：

- `summary.json`：整体、难度、领域、required hops 分组指标；
- `case_results.jsonl`：三种模式的逐题排序与指标；
- `report.md`：对比表和 hybrid 漏召案例。

GitHub Actions CI 运行同一评测，hybrid Recall@5 低于 0.84 时失败。门禁只用于防止仓库内回归，不是线上 SLA。

## 下一步生产升级

1. 将 `NumpyVectorIndex` 替换为真实中英文 embedding provider，但保留同一 evaluator。
2. 新建与开发集隔离的盲测集，至少覆盖中文改写、长查询、否定词、时间敏感问题和跨来源多跳。
3. 对 chunk size/overlap、BM25、dense embedding、RRF 或 reranker 做可控消融。
4. 大语料使用 FAISS/HNSW/Milvus/Qdrant 等 ANN，SQLite 继续保存 canonical evidence 与 lineage。
5. 对线上匿名查询采样并脱敏标注，建立 Recall、zero-result rate、latency 和 freshness 的长期监控。

第1步已完成并真实验证：`OpenAICompatibleEmbeddingProvider` 接入百炼 `text-embedding-v4`，支持batch、重试、归一化、usage telemetry和SQLite cache。真实结果与hashing冻结表分开保存，不覆盖原始离线基线。详见`docs/EMBEDDING_INTEGRATION.md`。
