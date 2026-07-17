# Open Source DeepResearch Comparison

这份文档用于解释本项目和常见开源 DeepResearch / research agent 项目的关系。目标不是复刻某个仓库，而是借鉴通用范式，并明确本项目的边界。

## Reference Projects

| Project | Actual data-source design | What this project borrows conceptually |
|---|---|---|
| [LangChain `open_deep_research`](https://github.com/langchain-ai/open_deep_research) | Tavily by default; configurable search APIs, MCP servers, and native model-provider web search | Search provider boundary and workflow-oriented DeepResearch framing |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | Web retrievers such as Tavily plus MCP for GitHub, databases, and custom APIs; supports hybrid `tavily,mcp` | Web/local/specialized source composition and cited reports |
| [STORM](https://github.com/stanford-oval/storm) | Internet search by default; `VectorRM` + Qdrant for a private corpus; releases FreshWiki and WildSeek datasets | Separate open-web retrieval, private-corpus retrieval, and evaluation data |
| [`dzhng/deep-research`](https://github.com/dzhng/deep-research) | Firecrawl search and content extraction; recursive breadth/depth loop | The smallest useful loop: query generation, search, extract, learn gaps, search again |
| [Tongyi DeepResearch](https://github.com/Alibaba-NLP/DeepResearch) | Serper for web/Google Scholar, Jina for page reading, DashScope for file parsing, sandbox tools, JSON/JSONL evaluation inputs | Search and page reading are separate tools; heterogeneous sources need explicit adapters |
| [SkyworkAI DeepResearchAgent](https://github.com/SkyworkAI/DeepResearchAgent) | Tools and stateful environments span filesystem, browser/mobile, and domain environments, with persistent memory/traces | Top-level planning plus specialized tools, environments, memory, and tracing |

## Shared Pattern

Most DeepResearch projects follow this coarse pipeline:

```text
question -> plan -> search -> read/extract -> synthesize report -> cite sources
```

More mature projects add:

- iterative search when evidence is missing;
- source quality or credibility ranking;
- multiple model/search providers;
- optional web search or crawling tools;
- streaming UI or web app packaging;
- benchmark or leaderboard evaluation.

## Current Project Position

This repository intentionally keeps the default path offline/local-first, then invests more engineering effort in traceability and reliability:

```text
question
-> Planner + DAGTaskGraph
-> Searcher / Reader
-> SQLite memory + numpy vector recall
-> TextRank quote-preserving compression
-> Writer with claim/citation structure
-> atomic Verifier
-> Red-Blue repair
-> ResearchBench-style offline evaluation
```

The main difference is not "better web search". The main difference is:

```text
claim -> citation -> evidence -> quote -> verification trace -> repair action
```

That chain is designed to be inspectable in code, SQLite, JSON reports, markdown showcase packs, and tests.

## What Was Added After Comparison

Six focused enhancements align the project more closely with open-source DeepResearch conventions without rewriting the stable core:

1. **Open-source comparison document**
   This file records the relationship between this project and common DeepResearch implementations, so interview discussion can be honest and grounded.

2. **Source quality scoring**
   Each `Evidence` now receives `metadata.source_quality`, `metadata.source_quality_band`, and `metadata.source_quality_signals`. The score is based on quote availability, quote-in-text validation, source trust level, source type, text length, and retrieval score.

3. **Optional lightweight iterative search**
   `ResearchCoordinator` can run a follow-up search when first-pass evidence is empty, low-quality, or quote-sparse. This is controlled by:

   ```powershell
   uv run python scripts/run_research.py "your question" --use-iterative-search
   uv run python scripts/run_showcase.py "your question" --use-iterative-search
   ```

   The default remains off to avoid mixing new behavior with frozen offline/mock benchmark metrics.

4. **Optional multi-source web search with persistent cache**
   Open-source DeepResearch agents commonly separate source discovery from source reading and support more than one retriever. This project now exposes `disabled`, `tavily`, `wikipedia`, `arxiv`, `github`, and `searxng`; provider names can be composed with commas. Tavily requests raw page content, Wikipedia offers MediaWiki extracts, arXiv returns paper abstracts, GitHub retrieves repository metadata and README, and SearXNG discovers URLs for bounded HTML/PDF extraction. Results use SQLite or Redis TTL cache with fallback, and final top-k preserves source diversity.

   ```powershell
   uv run python scripts/inspect_web_search.py "Deep Research" --provider wikipedia

   $env:TAVILY_API_KEY='your Tavily API key'
   uv run python scripts/run_research.py "your question" --enable-web-search --web-search-provider tavily
   uv run python scripts/run_research.py "your question" --config configs/live_web.toml
   ```

   Web results enter the same Searcher -> Reader -> Evidence -> Verifier path as local corpus results. The default remains disabled so local demos and benchmark runs stay reproducible.

5. **Component-level retrieval evaluation**
   The same 35 frozen questions now evaluate lexical/vector/hybrid ranking with Recall@K, MRR, nDCG, All-relevant@K and explicit failure cases. This separates Searcher quality from Writer/Judge behavior and provides a CI regression gate.

6. **Replaceable dense embedding path**
   Hashing remains the offline baseline, while an OpenAI-compatible batch embedding adapter adds normalization, retries, SQLite content/model cache and secret-free telemetry. No real embedding score is claimed until a configured provider is actually run.

## Honest Boundaries

- This project does not implement a headless-browser crawler. Tavily can return raw content, Wikipedia/arXiv/GitHub return structured content, and SearXNG pages use bounded HTML/PDF extraction with snippet fallback.
- Wikipedia is a keyless smoke/fallback source, not a substitute for time-sensitive web search; current or niche research should use Tavily or a configured SearXNG instance.
- It does not replace the custom Coordinator with LangGraph, CrewAI, or another framework.
- Source quality scoring is a lightweight heuristic, not a production credibility model.
- Iterative search is a one-step supplemental retrieval mechanism, not an autonomous long-horizon web research loop.
- Historical ResearchBench metrics should still be described as offline/mock metrics.
- The durable SQLite worker is a single-host execution design, not a replacement for Postgres plus Redis Streams/RabbitMQ/Kafka at multi-host scale.

## Interview Framing

If asked whether this project copied open-source DeepResearch agents:

> I studied common open-source DeepResearch patterns such as planning, search, source extraction, report synthesis, citations, and optional web tools. I did not clone a single project. My implementation focuses on the reliability layer that many simple demos do not expose: structured evidence memory, claim-level verification, Red-Blue repair, and offline evaluation. After comparison, I added source-quality metadata, one-step follow-up retrieval, composable Tavily/Wikipedia/SearXNG providers, source-diverse ranking, and a SQLite TTL search cache while keeping the benchmark path offline by default.
