# Week 07: TextRank Context Compression

本周目标是压缩上下文，同时保护引用证据。

核心学习点：

- L1 用 embedding 粗过滤候选句。
- L2 用 TextRank 句子图挑选高 salience 句子。
- L3 强制保留被引用 quote，避免压缩破坏验证链路。

当前代码入口：

- `src/deepresearch_agent/compression/textrank.py`

## 怎么观察

现在可以用固定样例观察压缩过程：

```powershell
uv run python scripts/inspect_compression.py --list
uv run python scripts/inspect_compression.py --case quote_preservation
uv run python scripts/inspect_compression.py --case multi_quote_preservation --json
```

学习样例在 `data/examples/compression_cases.jsonl`。

重点看：

- `original_char_count`：压缩前 evidence 总字符数。
- `compressed_char_count`：压缩后 selected sentences 总字符数。
- `compression_ratio`：压缩比例。
- `preserved_quote_count`：保留下来的引用 quote 数量。
- `selected_sentences[].preserved_quote`：某个句子是不是被 L3 quote protection 保留下来的。

## 为什么不用普通摘要

普通 summarizer 可能会把引用原句改写掉，这会破坏后面的 Verifier，因为 citation id 指向的 quote 不再出现在 Writer 上下文里。

当前设计分三层：

```text
L1 embedding 粗过滤候选句
L2 TextRank 在候选句里选高 salience 句子
L3 强制保留 citation quote
```

所以压缩目标不是“写得更短”，而是“在变短的同时不破坏证据链”。
