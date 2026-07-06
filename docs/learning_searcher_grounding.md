# Searcher Grounding 学习笔记

这份文档记录一次很典型的工程优化：Planner 已经能把“比较 SQLite 和向量数据库”识别成 `comparison`，但报告质量仍然不稳定。原因是 Planner 只负责“怎么拆问题”，不负责“证据是否找准”。

## 1. 为什么 Planner 不够

当前链路是：

```text
Question -> Planner -> DAG -> Searcher -> Reader -> Writer -> Verifier -> Red-Blue
```

Planner 做对之后，只说明任务图更合理。例如比较类问题会生成：

```text
定义比较对象和范围
  -> 收集方案 A 的优缺点
  -> 收集方案 B 的优缺点
  -> 比较 tradeoffs 和适用场景
  -> synthesize -> verify -> repair
```

但如果 Searcher 找到的是不相关 evidence，Writer 还是会写出空泛 claim，Verifier 也会把这些 claim 判成 `partial` 或 `unsupported`。

一句话：

```text
Planner 决定研究路线，Searcher 决定证据地基。
```

## 2. 暴露出来的问题

测试问题：

```powershell
uv run python scripts/run_research.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
```

优化前的现象：

- 报告结构已经是 comparison report。
- 但 evidence 会召回到 Cohen's d、简历材料、通用 Agent 语料。
- Writer 的比较类 claim 比较抽象。
- Verifier 会删除或修改弱支持 claim。
- `technical_comparison` 的 grounding 很低。

这说明系统不是“不会写比较报告”，而是“没有稳定找到比较所需证据”。

## 3. 这次怎么优化 Searcher

改动位置：

- `src/deepresearch_agent/agents/searcher.py`
- `data/corpus/offline_corpus.jsonl`
- `tests/unit/test_searcher.py`

核心思路是离线、可解释的 query expansion。

中文问题：

```text
比较 SQLite 和向量数据库的优缺点
```

会扩展出英文检索词：

```text
compare, comparison, tradeoffs, criteria,
vector, embedding, retrieval, similarity,
database, storage, memory
```

这样本地英文语料里的 `SQLite`、`vector retrieval`、`embedding similarity`、`hybrid memory design` 才能被稳定命中。

这不是 LLM 理解，也不是复杂搜索引擎，而是一个很适合学习的规则系统：

```text
用户词面 -> 领域词扩展 -> lexical/vector hybrid scoring -> top-k evidence
```

## 4. 为什么要补 corpus

只改 Searcher 还不够。检索系统的上限也取决于本地语料有没有对应知识。

这次新增了三篇离线文档：

- `sqlite_vector_tradeoffs`：SQLite 和 vector retrieval 分别解决什么问题。
- `vector_database_limits`：向量数据库/向量索引的优势和限制。
- `hybrid_memory_design`：SQLite 作为 source-of-truth，vector index 作为召回加速。

这三篇语料让比较类问题有了明确证据来源。

## 5. Writer 也必须更 grounded

Searcher 找准 evidence 后，Writer 不能继续写空泛 claim。

优化后的比较类 claim 更贴近 evidence：

```text
SQLite and vector retrieval solve different parts of an agent memory problem.
SQLite is strong for durable records, relational queries, audit trails, and exact traceability.
Vector retrieval is strong for semantic similarity, fuzzy recall, and reusing evidence across related queries.
```

这些 claim 的词和 evidence 明确对齐，因此 Verifier 能解释为什么它们是 `supported`。

## 6. Verifier 给出的反馈

优化后的同一问题：

```text
SQLite and vector retrieval solve different parts of an agent memory problem.
Matched 9/9 important terms.

SQLite is strong for durable records, relational queries, audit trails, and exact traceability.
Matched 10/10 important terms.

Vector retrieval is strong for semantic similarity, fuzzy recall, and reusing evidence across related queries.
Matched 11/12 important terms.
```

这就是 claim-evidence grounding 的闭环：

```text
相关 evidence -> grounded claim -> verifier trace -> supported
```

## 7. 本地评测观察

命令：

```powershell
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue
```

本地 offline/mock 观察：

- `redblue.judge_score_mean`: 0.881
- `redblue.weak_support_rate`: 0.490
- `redblue.atomic_support_rate`: 0.623
- `technical_comparison.judge_score_mean`: 1.000
- `technical_comparison.weak_support_rate`: 0.000
- `technical_comparison.atomic_support_rate`: 1.000
- `technical_comparison.evidence_grounding_score`: 0.684

注意：这些是离线 benchmark 内部对比指标，不代表真实线上模型能力。

## 8. 这次学到什么

这次优化可以总结成四句话：

1. Planner 把问题拆对，只是第一步。
2. Searcher 要把用户问题翻译成能命中语料的检索词。
3. Writer 的 claim 必须靠近 evidence，而不是靠近漂亮表达。
4. Verifier 的价值不是“打分”，而是暴露 claim 和 evidence 有没有真正对齐。

## 9. 你现在可以怎么复习

先观察 Planner：

```powershell
uv run python scripts/inspect_plan.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
```

再跑完整链路：

```powershell
uv run python scripts/run_research.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
```

重点看四件事：

- `plan type` 是否是 `comparison`。
- Evidence 里是否出现 `sqlite_vector_tradeoffs`、`vector_database_limits`、`hybrid_memory_design`。
- Key Claims 是否都有 citation。
- Verification trace 是否能解释 supported。

读代码顺序：

```text
planner.py -> searcher.py -> writer.py -> verifier.py -> blue_agent.py
```

今天先不用追求全部看懂。能讲清楚“为什么 Planner 拆得对还不够，Searcher 必须找得准”，这一阶段就很扎实了。
