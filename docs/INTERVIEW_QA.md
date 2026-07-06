# DeepResearch Agent Interview QA

这份文档用于把项目里的工程决策整理成面试问答。回答时不要背术语，重点讲：问题是什么、为什么这样做、替代方案是什么、怎么验证。

## Showcase

### Q: 如何证明这个项目不是一堆分散脚本，而是一条完整 DeepResearch 系统链路？

A: 我新增了 `run_showcase.py` 作为作品级入口。一条命令会从同一个 question 出发，生成 `plan.md`、`report.md/json`、`memory_trace.md`、`compression_trace.md`、`verifier_trace.md`、`redblue_trace.md`、`eval_summary.md` 和 `index.md`。这些产物对应规划、执行、记忆、压缩、验证、修复和评测，说明模块不是孤立存在，而是接在同一条离线可复现流水线上。

### Q: 为什么做 Markdown 展示包，而不是直接做 Web UI？

A: 当前目标是完成项目基座和学习闭环。Markdown/JSON 产物更轻量、可 diff、可测试，也更适合写博客和复盘工程过程。Web UI 后续可以接在这些稳定产物之上，但不应该先于底层链路。

## Planner

### Q: 为什么需要 Planner，而不是直接让一个 Agent 回答？

A: 复杂研究问题通常包含背景、证据、风险、评测和权衡。直接回答会把这些步骤藏在一个黑盒里，无法并发、无法追踪失败、也无法评测每一步。Planner 把问题拆成 `ResearchTask`，再由 DAG 表示依赖关系，后续 Coordinator 可以按拓扑批次并发执行。

### Q: 为什么保留 template 和 heuristic 两种 Planner？

A: Template Planner 稳定，适合作 baseline；Heuristic Planner 根据 comparison、risk analysis、solution design 等类型生成不同 DAG，更接近真实研究流程。保留两者可以做实验对比，而不是一上来就把所有规划交给 LLM。

### Q: 如果接真实 LLM Planner，现有设计还能用吗？

A: 能用。只要 LLM Planner 输出相同的 `ResearchPlan` 和 `ResearchTask` 结构，DAG、Coordinator、Memory、Eval 都不用改。这也是结构化 schema 的价值。

### Q: 为什么不用 LangGraph，而是手写 DAG 和状态机？

A: 我另一个项目已经用过 LangChain/LangGraph，所以这个 DeepResearch 项目的目标不是快速搭应用，而是学习底层 Agent 工程。手写 DAGTaskGraph 和 TaskStateMachine 可以把拓扑排序、并发批次、失败阻塞传播、状态转移这些机制真正讲清楚。后续如果迁移到 LangGraph，schema、memory、verifier 和 eval 仍然可以保留。

## Searcher

### Q: 你为什么做 query expansion？

A: 我发现 Planner 能把中文比较问题拆对，但 Searcher 找不到对应英文离线语料，导致 evidence 跑偏。query expansion 把“向量数据库 / 优缺点”扩展成 `vector / embedding / retrieval / tradeoffs`，让本地 corpus 能稳定命中。

### Q: 为什么不用真实搜索或 LLM 改写 query？

A: 当前阶段目标是离线可复现和学习底层机制。真实搜索会引入网络和排序波动；LLM 改写会掩盖检索逻辑。规则 expansion 虽然简单，但可测试、可解释，也能形成 baseline。

### Q: 怎么证明这次 Searcher 优化有效？

A: 同一个比较问题优化后能稳定召回 `sqlite_vector_tradeoffs`、`vector_database_limits`、`hybrid_memory_design`，Writer 生成的 3 个 comparison claims 都被 Verifier 判成 supported；评测里 technical_comparison 的 weak_support_rate 降到 0。

## Memory

### Q: 为什么同时用 SQLite 和 numpy vector index？

A: 两者职责不同。SQLite 是 source of truth，保存 runs、tasks、evidence、claims、reports、quote 和 metadata；numpy vector index 只负责相似召回，返回 evidence id。召回后还要回 SQLite 拿完整原文记录。

### Q: 为什么不直接用向量数据库？

A: 当前阶段要先学清楚底层机制。numpy index 足够展示 embedding、cosine similarity、top-k recall 和 id 回表。等接口稳定后，可以把 NumpyVectorIndex 替换成 FAISS/Chroma/向量数据库，但 SQLite 的审计链路仍然需要保留。

### Q: 怎么证明记忆链路可追踪？

A: `inspect_memory_trace.py` 会把 evidence 写入临时 SQLite 和 numpy index，然后用 query 召回相似 id，再通过 `get_evidence(id)` 回表拿到 title、source_id、chunk_id、quote。这说明 vector 只负责找候选，SQLite 负责可审计记录。

### Q: SQLite 和 vector index 为什么不合成一个组件？

A: 因为它们解决的问题不同。vector index 追求相似召回，返回的是候选 evidence id；SQLite 追求可审计，保存完整 quote、source、chunk、run、task 和 claim。把两者分开后，召回策略可以替换，审计链路不受影响。

## Verifier

### Q: 为什么要拆 atomic claims？

A: 长 claim 可能包含多个事实。整体 overlap 可能把部分支持误判成完全支持。Atomic verification 把一句话拆成小事实，分别选择 best evidence，再聚合状态。例如 mixed case 中，一半 supported、一半 unsupported，整体就应该是 partial。

### Q: Verifier 怎么选择 best evidence？

A: 当前是离线启发式：`term_overlap * 0.65 + quote_overlap * 0.25 + source_trust * 0.10`。这样能同时考虑 claim 和 evidence 的术语重叠、quote 是否覆盖关键内容、来源可信度。

### Q: 这算真正的事实验证吗？

A: 还不算严格 NLI。当前是可解释的第一版 heuristic verifier，适合离线学习和回归测试。后续可以把 LLM verifier 或 NLI 模型作为第二层，但第一层规则能提供稳定 baseline 和 debug trace。

### Q: 为什么不直接用 LLM-as-Verifier？

A: 真实 LLM verifier 输出会受模型、prompt、温度和网络影响，不适合作为早期回归测试。当前 heuristic verifier 虽然能力有限，但每个 decision 都有 term overlap、quote overlap、best evidence 和 missing terms，便于定位问题。后续可以把 LLM verifier 放在第二层，而不是替代可解释 baseline。

## Compression

### Q: 为什么需要上下文压缩？

A: DeepResearch 会产生很多 evidence，如果全部塞给 Writer，会增加成本，也会让关键信息被噪声淹没。压缩模块把 evidence 变成更短的 `CompressedContext`，让 Writer 只读高价值句子。

### Q: 为什么不是直接让 LLM 总结 evidence？

A: 普通总结可能改写或丢掉 citation quote，而后续 Verifier 需要 quote 来做 claim-evidence 对齐。当前设计是 L1 embedding 粗过滤、L2 TextRank 选高 salience 句子、L3 强制保留 citation quote，先保证证据链不被破坏。

### Q: 怎么验证 quote 没丢？

A: 我做了固定 compression cases。比如 `multi_quote_preservation` 在 `max_sentences=1` 时仍然保留 2/2 个 quote，说明 L3 quote preservation 会覆盖普通句子数量限制。

## Red-Blue

### Q: Red-Blue 和普通 self-reflection 有什么区别？

A: Red-Blue 把“反思”工程化了。Red 输出结构化 `AttackFinding`，包含 category、severity、target、reason；Blue 只能执行 ADD、DELETE、MODIFY、VERIFY 等明确动作，并记录 before/after。这样修复过程可测试、可评测、可复盘。

### Q: 什么时候 DELETE，什么时候 MODIFY？

A: 无 citation 的强断言、unsupported 或 contradicted 且高 severity 的 claim 会 DELETE；partial 或过度概括的 claim 会 MODIFY，加上更谨慎的 wording；omission 会 ADD limitation；已经 supported 且 Red 没发现问题的 claim 不修。

### Q: 做 Red-Blue 学习样例时发现了什么问题？

A: no-citation case 里，报告没有 evidence，但 Red 仍然追加了 omission finding，导致 DELETE 后又 ADD limitation。这个规则不合理，所以把 omission 检查改成只有 report.evidence 非空时才触发。这是一个真实工程调试例子。

## Evaluation

### Q: 为什么要做离线 ResearchBench？

A: 如果只展示几个好看的报告，很难证明系统是否稳定。离线 benchmark 能比较 baseline、verifier、redblue 等配置，并输出 weak_support_rate、atomic_support_rate、repair_precision、Bootstrap CI、Cohen's d 等指标。

### Q: 这些指标能不能写成线上效果？

A: 不能。当前是 mock/offline benchmark，只能说明本项目内部配置的可复现对比，不能当作真实用户场景或线上模型效果。简历中应该写“离线评测集上的可复现实验结果”。

### Q: Bootstrap 95% CI 是做什么的？

A: 它用重采样估计 judge score 均值的不确定性。因为我们的 benchmark 规模有限，单个均值可能不稳定，CI 能告诉我们这个均值大概会落在哪个区间里。

### Q: Cohen's d 和均值提升有什么区别？

A: 均值提升只说明 improved 比 baseline 高多少；Cohen's d 会把差值除以 pooled standard deviation，表示提升相对波动有多大。它更像效果量，帮助判断提升是不是有实际意义。

## LLM Backend

### Q: 你这个项目真的支持多个 LLM 后端吗？

A: 工程接口支持。项目定义了统一 `LLMBackend` 协议，并用 `LLMBackendConfig -> create_llm_backend()` 创建 Mock、OpenAI、DeepSeek、vLLM 后端。默认 mock 离线跑通；真实后端只在显式配置 API key 和 backend 时启用。

### Q: 为什么 DeepSeek 默认选 `deepseek-v4-flash`？

A: 这个项目的真实模型调用只用于低成本 showcase，不参与正式 benchmark。`deepseek-v4-flash` 是当前 DeepSeek 官方低成本模型，适合做单题真实 API 验证；脚本会用 `max_tokens` 控制输出长度，并记录 token usage 和 estimated cost。

### Q: 为什么默认不用真实 LLM？

A: 这个项目早期目标是学习底层 Agent 工程。真实 LLM 会带来 API 成本、网络波动和输出不确定性，容易干扰 DAG、Memory、Verifier、Evaluation 这些基础模块的可复现测试。所以默认 mock，真实模型作为后期增强。

### Q: API key 怎么管理？

A: API key 只从环境变量读取，例如 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY`、`VLLM_API_KEY`，不写入代码或配置文件。`inspect_llm_backend.py` 可以 dry-run 检查 env 是否配置，不访问网络。
