# SQLite + numpy 向量记忆

核心观点：Agent memory 不是聊天记录，而是可查询、可审计、可复用的运行轨迹。

SQLite 在这个项目里承担共享记忆层。runs 保存一次研究任务，tasks 保存 DAG 节点状态，evidence 保存 source/chunk/quote，claims 保存报告结论，reports 保存最终 JSON 和 Markdown，agent_events 保存每个 Agent 的耗时和错误，verification_traces 保存 claim-evidence 对齐过程，repair_actions 保存 Red-Blue 修复记录。

Evidence 是记忆的核心对象。一个 evidence 不只是文本片段，还包含 source_id、chunk_id、quote_start、quote_end、score 和 metadata。这样任意 claim 都能追溯到引用，再追溯到原始 source chunk。这种追踪能力是“可信研究报告”和“普通生成答案”的关键区别。

向量索引用 numpy 实现，而不是一开始就接向量数据库。hashing vectorizer 虽然简单，但足够解释 embedding 相似检索的原理：文本变成固定维度向量，归一化后用矩阵乘法计算 cosine similarity。SQLite 存原文，numpy index 存召回入口，两者配合完成 memory recall。

这条设计路线适合学习：先理解检索和记忆的底层机制，再考虑 FAISS、Milvus 或在线 embedding API。项目里的 evidence_reuse_rate 可以衡量历史记忆被复用的比例，帮助判断 memory 是否真的参与了研究过程。
