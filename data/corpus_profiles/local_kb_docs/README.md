# Local Knowledge Base Demo

这个 profile 模拟企业知识库式 RAG 场景：把本地 Markdown、TXT、HTML 或 PDF 资料放进同一个目录，运行 `uv run python scripts/build_corpus_profiles.py --profile local_kb_docs` 后会生成 Searcher-compatible JSONL corpus。

适合演示的问题包括：

- 如何把本地资料转成可追踪 evidence chunk？
- 为什么 claim 需要绑定 citation 和 quote？
- PDF/Markdown 混合资料如何进入同一条 Agent pipeline？

当前 profile 用作稳定作品展示，不做线上上传、多租户权限或全网搜索。
