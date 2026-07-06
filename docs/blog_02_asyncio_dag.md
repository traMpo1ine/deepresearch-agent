# asyncio + Semaphore + DAG 编排

核心观点：DeepResearch 的复杂性不只在模型，而在任务依赖和并发控制。

复杂研究问题通常不是线性的。一个问题可能同时需要背景概念、实现机制、风险分析、评测指标和工程权衡。Planner 把这些子问题变成 ResearchTask，再由 DAGTaskGraph 表达依赖关系。没有依赖的任务可以处于同一个拓扑批次中并发执行，依赖未完成的任务必须等待。

asyncio 负责并发，Semaphore 负责节制。Searcher 和 Reader 这类 IO-heavy 任务适合并发，但如果完全放开，会让本地资源或外部 API 被打爆。Semaphore 给系统一个明确的并发上限，让 throughput 和稳定性之间有可控平衡。

状态机让失败变得可见。任务从 PENDING 到 READY，再到 RUNNING、SUCCEEDED 或 FAILED；如果上游失败，下游进入 BLOCKED。这样 report 或 SQLite 里能解释“为什么某个任务没有执行”，而不是静默少了一块研究内容。

本项目的 run_summary 汇总了任务数、成功数、失败数、阻塞数、重试数、平均耗时和 evidence 数。面试时可以从一次 run summary 讲清楚：系统做了哪些任务，哪些任务并发，失败如何传播，为什么这比单次 prompt 更像真实工程。
