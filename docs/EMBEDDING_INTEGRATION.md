# 真实 Embedding 接入与缓存

## 目标

原始 Searcher 固定使用 64 维 hashing vector。它无网络、确定性强，适合学习 cosine similarity 和做 CI，但并不理解真正语义。本次改造保留 hashing 作为默认 fallback，同时把 OpenAI-compatible `/embeddings` 接进 Searcher 主链路和检索 evaluator。

## 数据流

1. Searcher 对 query 做规则扩展，并收集当前候选文档文本。
2. provider 一次接收 query + documents，按配置拆 batch；百炼 `text-embedding-v4` 会自动把请求上限钳制到官方限制的 10 条。
3. 先用 `SHA-256(base_url + model)` 隔离 namespace，再用文本 SHA-256 查询 SQLite cache。
4. 只把缺失文本发送到 `/embeddings`；API key 只从 `EMBEDDING_API_KEY` 或用户指定的环境变量读取。
5. 校验返回数量、index 顺序、有限数值、非零向量和统一维度，然后做 L2 normalization。
6. Searcher 用 cosine similarity 参与 hybrid ranking；run summary 记录 provider/model、cache hit/miss、请求数、重试和最近延迟，不记录 key 或完整输入。

缓存使用 WAL、`busy_timeout=5000` 和原子 upsert。embedding 对给定模型与输入是可复用派生数据，因此不设置短 TTL；更换 base URL 或 model 会自动进入新 namespace。删除 `data/memory/embedding_cache.sqlite3` 可强制重建。

## 配置

默认配置完全离线：

```toml
embedding_provider = "hashing"
```

真实兼容服务：

```powershell
$env:EMBEDDING_API_KEY='你的 key'
uv run python scripts/run_research.py "比较 SQLite 与向量检索" `
  --embedding-provider openai-compatible `
  --embedding-base-url 'https://你的兼容服务/v1' `
  --embedding-model '你的 embedding 模型'
```

检索消融同样支持这些参数。建议先跑 hashing 冻结基线，再换真实 provider 输出单独目录，不覆盖 offline 指标。

## 已验证与未验证

已验证：

- batch 输入、去重、顺序恢复、L2 normalization；
- SQLite 跨调用命中，同一文本不重复发请求；
- response 数量/维度/零向量异常处理；
- API key 只显示 `env_configured`，状态 JSON 不泄漏 secret；
- Searcher 能通过 async provider 完成 vector 排序；
- hashing 默认主链路与 35 题回归指标保持不变。
- 阿里云百炼 `text-embedding-v4` 返回1024维真实向量；
- 35题真实 vector Recall@5 0.943、Hit@5 1.000、MRR@5 0.910；
- 相对64维 hashing vector，15题Recall@5改善、0题退化；
- 正式首跑37次批量请求、58个唯一输入、1706 tokens、0重试、0错误；
- 同缓存复跑0远程请求、1680 cache hits、0 cache misses。
- 80 条冻结 held-out v1（47 中文/33 英文、40 条多跳）上，真实 vector Recall@5 0.920、Hit@5 0.988、MRR@5 0.915；hashing vector Recall@5 仅0.371；
- held-out 真实 vector 中文 Recall@5 0.925、英文 Recall@5 0.912，说明多语种 dense signal 明显优于 hashing；
- held-out 首跑103个唯一输入、3285 tokens、82次请求、0重试/0错误；报告完整保留13个失败案例；
- 首次用默认64条请求时百炼返回HTTP 400；适配器现按 base URL + model 自动将 `text-embedding-v4` effective batch size限制为10，并分别记录requested/effective batch size。

未验证：

- 不同兼容服务的限流、token 上限和 dimensions 参数可能不同；
- 当前 cache 是单机 SQLite，不是多机共享特征库；
- 没有实现 ANN，23 文档基准仍是暴力 cosine，复杂度约为 O(Nd)。

开发集正式报告：`reports/retrieval_eval/dashscope_text_embedding_v4_formal_v1/report.md`。独立冻结集报告：`reports/retrieval_eval/holdout_v1_dashscope/report.md`。按百炼同步/批量计价口径不同，本项目只冻结实际 token usage，不把估算价格当系统指标。

## 面试可讲的工程取舍

- 为什么缓存 key 必须包含 model：同一文本被不同模型编码后维度和向量空间不同，不能混用。
- 为什么先归一化：归一化后的内积等价于 cosine similarity，避免向量模长影响排序。
- 为什么真实 embedding 结果必须单独报告：provider、模型和数据版本都会影响结果，不能与 hashing/offline 指标混写。
- 为什么 SQLite 仍保留：embedding cache 和 ANN 只是派生加速层，canonical evidence、citation lineage 与 run state 仍需要关系型存储。
