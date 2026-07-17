# Service Operations and Persistent Run State

这份文档说明 Web Demo 如何从进程内字典升级为可重启恢复、可审计的任务状态服务，以及它与 Redis、真正分布式任务队列之间的边界。

## 状态链路

```mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI worker
    participant S as WAL SQLite DemoRunStore
    participant B as Background task

    C->>A: POST /api/runs + X-Request-ID
    A->>S: BEGIN IMMEDIATE / idempotency + capacity / INSERT queued
    A-->>C: run_id / queued
    B->>S: UPDATE queued -> running WHERE status=queued
    alt exactly one worker claims the run
        B->>B: build_showcase
        B->>S: UPDATE running -> succeeded/failed
    else duplicate dispatch
        B-->>B: claim returns no row; stop
    end
    C->>A: GET /api/runs/{run_id}
    A->>S: SELECT by primary key
    A-->>C: persisted status and artifact paths
```

## 为什么不能继续用全局字典

进程内 `dict` 只适合最小 Demo：进程重启后数据消失；两个 Uvicorn worker 看到不同字典；状态更新没有事务，重复调度可能执行两次。`DemoRunStore` 把 run id、request id、输入配置、输出目录、状态、错误与时间戳写入 SQLite。

## SQLite 设计

- `run_id` 是主键，避免任务重复创建。
- `status` 有 CHECK constraint，只允许 `queued/running/succeeded/failed`。
- `queued -> running` 使用 `UPDATE ... WHERE status='queued'`，以受影响行数决定是否领取成功。
- `running -> succeeded/failed` 同样使用条件更新，非法状态转移直接失败。
- `(status, updated_at)` 复合索引支持状态列表和陈旧任务扫描。
- WAL 模式允许读请求与单写者更好地并行；`busy_timeout=10s` 吸收短时写锁竞争。
- `PRAGMA user_version` 记录 schema 版本，遇到比代码更新的数据库会拒绝启动，避免静默误读。
- 当前 schema version 为 4，保留真实的 v1/v2/v3→v4 migration：先补唯一 `idempotency_key` 和 `request_fingerprint`，再增加 `worker_id`、`lease_expires_at` 与 `attempt_count`。
- 服务启动时将超过一小时仍处于 queued/running 的记录标为 `worker_interrupted_or_lease_expired`。

## 幂等与背压

客户端可能因为网络超时重试 `POST /api/runs`。服务接受 1–128 字符的安全 `Idempotency-Key`，并对规范化 Pydantic payload 做 SHA-256 指纹：

- key 和指纹都相同：返回已有 run，HTTP 200，并设置 `X-Idempotent-Replay: true`；
- key 相同但指纹不同：HTTP 409，防止一个 key 被误用于不同任务；
- 首次请求：HTTP 202，在同一 `BEGIN IMMEDIATE` 事务中检查容量并插入 queued run；
- queued + running 达到 `DEMO_MAX_ACTIVE_RUNS`：HTTP 429 与 `Retry-After: 5`。

容量检查和插入必须在同一写事务中，否则两个并发请求都可能看到“还剩一个名额”并同时进入。单元测试用两个线程同时 admit，在容量 1 时只允许一个成功。

## SQLite 与 Redis 的分工

| 组件 | 当前职责 | 为什么 |
|---|---|---|
| SQLite run store | Demo run canonical state、错误、配置和恢复 | 需要持久、可审计、可回表 |
| SQLite memory | tasks/evidence/claims/traces/repairs | 研究事实链需要事务与长期保存 |
| Redis | Web search TTL cache | 数据可重新抓取，允许过期和淘汰 |
| 进程内内存 | 当前请求对象、短生命周期计算 | 不作为跨请求事实来源 |

不能因为“Redis 更快”就把所有数据放进 Redis，也不能因为 SQLite 简单就声称它适合无限水平扩展。当前写入规模小、单机作品演示占主导，SQLite 是合理选择。

## API 与可观测性

- `GET /api/health/live`：进程存活。
- `GET /api/health/ready`：静态资源、corpus、报告目录和 run store 均可用。
- `GET /api/health`：额外返回 run-store backend、路径、状态计数和启动恢复数量。
- `GET /metrics`：Prometheus 0.0.4 文本，输出请求计数、累计耗时、uptime、各 run status、active 数和 capacity。
- `GET /api/runs?status=succeeded&limit=20`：查看最近任务。
- `GET /api/runs/{run_id}`：跨应用重启读取单个任务。
- 所有响应携带 `X-Request-ID`，任务表和 JSON 日志保存同一 request id。

HTTP metric label 使用 FastAPI route template，例如 `/api/runs/{run_id}`，而不是实际 run id；404 统一为 `/__unmatched__`。这是为了避免每个任务产生一个新时间序列。`ServiceMetrics` 使用线程锁保证同一进程并发更新不丢失，但它不是跨进程聚合器：HTTP counter/latency 属于单 worker；run status gauge 每次从共享 SQLite 查询，因此是数据库级视图。多 worker 部署应让 Prometheus 分别抓取各 worker，或改用支持 multiprocess 的指标后端。

## 已验证的故障场景

1. 四个线程同时 claim 同一 run，只有一个成功。
2. 完成任务后重新创建 `FastAPI` 应用，仍能读取原 run 和 artifacts。
3. 超过阈值的 queued/running run 被恢复为 failed，而不是永久假运行。
4. queued 状态直接 finish、未知 status 等非法转换会被拒绝。
5. readiness 实际执行 SQLite 查询，不只检查数据库文件是否存在。
6. 相同 Idempotency-Key 的相同 payload replay 到同一 run，不同 payload 返回 409。
7. 两个并发 admit 在容量 1 时只有一个进入，另一个得到 capacity error。
8. 200 次多线程 HTTP counter 更新无丢失，路由模板不会把 run id 放进 label。

## 仍然保留的工程边界

FastAPI `BackgroundTasks` 仍由接收请求的进程执行；SQLite 解决了状态共享与幂等领取，但不是消息队列。它没有独立 worker 调度、心跳续租、优先级、延迟任务、自动重投或 dead-letter queue。

如果要升级为多机服务，推荐：API 将 job 写入 Postgres/SQLite 并投递到 Redis Streams、RabbitMQ 或 Kafka；独立 worker 使用 lease/heartbeat 执行；超时任务由 scheduler 回收；artifact 写对象存储。Go search gateway 应保持为独立外部检索服务，不接管 DeepResearch 的 canonical run state。

当前仓库已经补充单机独立 worker：SQLite schema v4 记录 `worker_id`、`lease_expires_at`、`attempt_count`，支持 FIFO 原子领取、ownership heartbeat、过期重排和有界失败；Compose 拆为 app/worker。它解决 API 与执行进程耦合，但没有把单机 SQLite 包装成跨主机队列，完整操作见 `docs/DURABLE_WORKER_OPERATIONS.md`。
