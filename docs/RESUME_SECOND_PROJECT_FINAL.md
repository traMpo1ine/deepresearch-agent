# DeepResearch Agent 简历第二项目最终版

目标岗位：AI Agent / RAG / AI 应用开发 / LLM 应用工程日常实习。

GitHub：`https://github.com/traMpo1ine/deepresearch-agent`

## 简历项目标题

**DeepResearch Agent：面向复杂调研任务的可追踪多 Agent 可信生成系统**

独立开发 / 个人项目

技术栈：Python, FastAPI, asyncio, SQLite/Redis, Docker Compose, Tavily/MediaWiki/arXiv/GitHub/SearXNG, numpy, TextRank, DeepSeek API, pytest, GitHub Actions

## 推荐简历 Bullet

- 独立开发 DeepResearch Agent Web Demo；将进程内任务字典升级为 WAL SQLite durable run store，实现 Idempotency-Key + payload 指纹、原子容量准入及 409/429 语义；进一步拆分 API/worker，支持 FIFO 原子领取、worker ownership heartbeat、lease expiry 重排和有界失败，并补充健康探针、X-Request-ID、JSON 日志、低基数 Prometheus 指标和非 root Docker Compose + Redis 部署。
- 设计 Planner + DAGTaskGraph + TaskStateMachine + Coordinator 多 Agent 编排框架，将复杂调研问题拆解为拓扑依赖任务图，并通过 asyncio + Semaphore 执行同层任务，记录 queued/running/succeeded/failed/blocked/timeout 等任务状态。
- 构建可追踪 RAG 数据链路，支持 Web 流式上传 PDF/Markdown/TXT/HTML、大小与格式校验、SHA-256 内容寻址去重和原子 corpus 发布；实现 PDF 逐页切块与 page-aware stable id，真实 6 页 ASCC 论文生成 64 chunks，上传后 run 产出 16 条带页码/upload lineage 的 Evidence，使 claim -> citation -> page -> chunk -> quote 可追溯。
- 构建可插拔真实检索层，组合 Tavily 原始正文、MediaWiki、arXiv、GitHub README 与 SearXNG，完成 HTML/PDF 安全读取、SSRF 防护和 source diversity；实现 Provider 并发限制、超时重试、熔断及结构化遥测，支持 Redis TTL cache 故障回退 WAL SQLite；12 个真实联网案例全部通过，lineage/transport telemetry/二次缓存命中率均为 1.000。
- 实现 atomic Verifier 与 Red-Blue 对抗修复机制，支持 ADD/DELETE/MODIFY/VERIFY repair action、repair loop 收敛/震荡/最大轮数 trace；80 条 adversarial fixtures 上 repair_success 从 0.425 提升到 1.000，repair_precision 达到 1.000。
- 构建 ResearchBench-style 离线评测体系，覆盖 35 题冻结主集、10 题 adversarial suite、60 题 extended ablation 与 80 条 Red-Blue fixtures；60 题 extended benchmark 中 baseline judge mean 0.764 -> full 0.880，weak_support_rate 1.000 -> 0.431，full repair_precision 0.944、repair_coverage 1.000。
- 建立 Searcher 独立检索回归：复用 35 题人工 `required_sources` 标签，对 lexical/vector/hybrid 运行 Recall@K、MRR、nDCG 和多跳 All-relevant@K 消融；hybrid Recall@5 0.843、Hit@5 0.943、MRR@5 0.852，并将 Recall@5 >= 0.84 接入 GitHub Actions，报告同时保留 9 个漏召案例和 hashing vector 局限。
- 为 Searcher 增加可插拔 OpenAI-compatible embedding adapter，实现模型感知batch上限、重试、L2归一化、模型/内容寻址WAL SQLite cache和usage telemetry；另建80条冻结held-out v1（47中文/33英文、40条多跳），百炼 `text-embedding-v4` vector Recall@5 0.920、MRR@5 0.915，显著高于hashing vector的0.371，中文Recall@5达到0.925。
- 固化真实数据黄金案例：读取NIST、OWASP、arXiv三类公开来源，以真实Embedding生成29条Evidence，3条主张分别绑定真实URL并产出verification trace，source lineage完整率1.000；无生成模型Key时使用确定性extractive writer，并为DeepSeek保留受约束LLM writer模式。
- 接入 DeepSeek OpenAI-compatible provider 与 formal LLM verifier benchmark，以 `deepseek-v4-flash` 对 120 个 balanced claim/evidence cases 重复 3 轮共 360 次真实判断，accuracy 0.842、macro-F1 0.831，并将真实 API 输出与 offline/mock benchmark 指标隔离。

## 更短版本

如果简历空间紧张，用下面 4 条：

- 独立开发 DeepResearch Agent Web 系统，支持流式上传 PDF/Markdown/TXT/HTML 和 Tavily/Wikipedia/arXiv/GitHub/SearXNG 真实检索；实现 SSRF 防护、页码级 citation lineage、Redis TTL cache → WAL SQLite fallback，12 个真实联网案例全部通过。
- 设计 Planner + DAGTaskGraph + TaskStateMachine + Coordinator 多 Agent 编排；将 API/worker 解耦到 SQLite schema v4 durable queue，实现幂等准入、FIFO 原子领取、heartbeat/lease recovery，并完成 queued→succeeded→artifacts 的独立进程 E2E。
- 实现 atomic Verifier 与 Red-Blue 修复，支持 ADD/DELETE/MODIFY/VERIFY 和收敛 trace；80 条 adversarial fixtures 上 repair_success 0.425→1.000、repair_precision 1.000，使 claim→citation→page/chunk→quote→verification 可追踪。
- 构建生成与检索双层评测：60题extended ablation中judge mean 0.764→0.880、weak_support_rate 1.000→0.431；80条冻结held-out上真实vector Recall@5 0.920、MRR@5 0.915，并保留语言/查询风格/多跳分层与13个失败案例。

## 一句话介绍

这个项目不是单次 LLM 问答 Demo，而是一个离线可复现的 DeepResearch Agent 工程系统：用户问题先被 Planner 拆成 DAG，多 Agent 执行后把 evidence 写入 SQLite 和向量索引，Writer 基于压缩上下文生成带 citation 的报告，再由 Verifier 和 Red-Blue 模块做 claim 级验证与修复，最后用 ResearchBench-style benchmark 输出可复查指标。

## 3 分钟面试讲稿

我做这个项目的动机是：普通 RAG Demo 通常只展示一次问答结果，但复杂调研任务真正难的是“能不能追踪证据、发现弱支持 claim、修复幻觉，并用指标证明改进”。所以我把系统拆成了规划、执行、记忆、压缩、验证、修复和评测七条链路。

用户问题进入系统后，Planner 会生成 ResearchTask DAG，Coordinator 按拓扑批次并发执行 Searcher 和 Reader。每个 evidence 会写入 SQLite，同时进入 numpy hashing vector index，保证后续 claim 可以回溯到 source chunk 和 quote。Writer 不直接吃全部 evidence，而是先经过 TextRank 压缩，并强制保留 citation quote，避免压缩破坏验证链路。

可信生成部分，我实现了 atomic Verifier，把长 claim 拆成 atomic claims，为每条 claim 选择 best evidence，并记录 verification trace。之后 Red Agent 从事实性、逻辑一致性、引用质量、遗漏信息攻击报告，Blue Agent 只能用 ADD/DELETE/MODIFY/VERIFY 做修复，并记录 repair loop 的收敛、震荡和停止原因。

评测上，我做了 35 题冻结 ResearchBench、10 题 adversarial suite、60 题 extended ablation 和 80 条 Red-Blue fixtures。60 题 extended benchmark 中 baseline judge mean 从 0.764 提升到 full 0.880，weak_support_rate 从 1.000 降到 0.431；80 条 fixtures 上 repair_success 从 0.425 到 1.000。我还用 DeepSeek 做了 360 次 verifier 判断，accuracy 0.842、macro-F1 0.831，但这部分只作为 verifier benchmark，不混入 offline/mock 主指标。

为了避免只评最终回答，我又把 Searcher 单独拉出来做 Recall@K/MRR/nDCG 消融，并新建80条一次性冻结held-out。真实百炼vector Recall@5是0.920，中文达到0.925，同时保留13个漏召案例；旧hashing在这批新问题上只有0.371，说明独立测试能暴露开发集没有暴露的问题。服务层把API和执行拆成独立worker，使用SQLite ownership/lease/heartbeat；本地E2E真实跑通queued到succeeded和artifacts。

## 8 分钟展开结构

1. 项目动机：从普通 RAG Demo 升级到可追踪、可验证、可修复、可评测的 Agent 系统。
2. 编排链路：Planner -> DAGTaskGraph -> TaskStateMachine -> Coordinator。
3. RAG 链路：Searcher / Reader -> SQLite memory -> numpy vector recall -> citation quote。
4. 可信链路：TextRank compression -> atomic Verifier -> Red-Blue repair loop。
5. 评测链路：ResearchBench-style benchmark、adversarial suite、Bootstrap CI、repair metrics。
6. 工程包装：FastAPI Web Demo、GitHub Actions CI、Demo GIF、traceability matrix。
7. 边界说明：offline/mock 指标不等于线上效果，DeepSeek 真实调用只做 provider/verifier showcase。

## 面试官可能追问

**Q：为什么默认用 mock/offline，而不直接全用真实 LLM？**

A：这个项目优先验证 Agent 工程链路和评测闭环。mock/offline 能保证结果可复现、可回归、成本稳定；真实 DeepSeek 被单独放在 provider smoke 和 verifier benchmark 里，证明 provider 接入与成本边界，但不污染主指标。

**Q：你的 Verifier 是不是严格 NLI？**

A：不是。主链路里的 atomic Verifier 是启发式 claim-evidence 对齐，用来做可解释 trace 和 repair 触发；我额外做了 DeepSeek formal verifier benchmark 作为二级语义判断补强，但仍然不把它包装成生产级 NLI。

**Q：这个项目和普通 RAG 的区别是什么？**

A：普通 RAG 更关注检索和回答，这个项目更强调完整研究链路：任务规划 DAG、证据记忆、引用保护、claim 级验证、Red-Blue 修复和 benchmark 指标。输出不是一段答案，而是一套可追踪报告生成流程。

**Q：数据来源支持什么？**

A：离线路径支持 Markdown/TXT/HTML/PDF corpus profile，其中文本型 PDF 按页切块并保留 `p. N` locator；已用真实 6 页论文生成 64 个 chunks。显式联网后可组合 Tavily、Wikipedia、arXiv、GitHub 和 SearXNG，保留内容 hash、抓取时间、attempt/retry/latency/circuit state，并通过 Redis/SQLite cache 进入统一 citation/verifier 链路。12 个 live cases 已真实运行通过；当前不做 OCR、多租户权限或 headless-browser JavaScript 渲染。

## 投递关键词

AI Agent, Multi-Agent, RAG, DeepResearch, LLM Application, FastAPI, SQLite Memory, Vector Retrieval, TextRank, Verifier, Red-Blue Repair, LLM-as-Judge, DeepSeek, Evaluation, GitHub Actions

## 必须诚实说明的边界

- offline/mock benchmark 是项目内部可复现对比，不代表线上用户场景。
- DeepSeek 真实调用只用于 provider smoke 和 verifier benchmark，不参与主链路指标。
- 默认离线回归仍使用numpy hashing baseline；真实百炼Embedding已接入并单独冻结报告。
- 35 题检索集同时用于项目评测与权重校准，不是独立盲测集；0.843 是仓库内回归基线，不能外推为线上检索准确率。
- 80条held-out v1与开发问题分开编写且未用于调参，但仍是个人项目内人工标注、复用23文档corpus，不是第三方公开benchmark，不能外推成线上准确率；公开后v1也不能再用于调参后继续称为盲测。
- 黄金案例的真实来源、Embedding、citation和verification均已实跑；当前生成端是确定性extractive writer，不是DeepSeek生成。DeepSeek主链路writer代码已实现，但尚未用真实Key跑通，不写成已完成真实LLM全链路。
- 当前 Web Demo 是本地作品展示，不是多用户 SaaS。
- SQLite run store 提供跨 worker 状态可见性和幂等领取，但 FastAPI BackgroundTasks 仍不是带独立 worker、heartbeat 与 dead-letter queue 的分布式任务系统。
- Dockerfile/Compose 已完成文件级与 API 探针测试，但当前开发机未安装 Docker CLI，尚未做真实镜像 build。
- durable worker 当前是单机共享 SQLite/volume，不是跨主机分布式队列；生产升级需 Redis Streams/RabbitMQ/Kafka + Postgres + object storage。
- 真实检索默认关闭；当前 live-source 结果是 12 个真实案例，不代表生产 SLA。
- 已配置每周 live-source monitor 与滚动趋势报告，但目前只有 1 个真实历史观测，简历仍只写 12-case 实跑结果，不写长期可用率。
- 当前不含多租户权限、登录态抓取或 headless-browser JavaScript 渲染；上传是本地单用户模式，无杀毒/OCR/总存储配额。

## 投递前检查

- GitHub 仓库应设为 Public。
- README 顶部应能看到 CI badge、Demo GIF、关键结果和证据入口。
- Actions 页 CI 应至少有一次成功 run。
- 简历链接建议写：`GitHub: github.com/traMpo1ine/deepresearch-agent`
- 若匿名访问 `https://github.com/traMpo1ine/deepresearch-agent` 仍返回 404，重新检查仓库 visibility、owner/repo 拼写和是否需要等待 GitHub 权限生效。
