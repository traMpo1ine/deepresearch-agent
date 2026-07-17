# Durable Demo Worker 运行手册

## 为什么从 BackgroundTasks 拆出来

FastAPI `BackgroundTasks` 适合本地演示，但任务和 API 进程同生共死：API 重启会中断执行，也不能独立扩容 worker。worker 模式把 API 变成 producer，把 SQLite run store 变成持久化队列与状态事实源，独立进程负责 consumer/executor。

## 状态与租约

```text
API admit: queued
worker claim_next: queued -> running (worker_id, lease_expires_at, attempt_count + 1)
heartbeat: running -> running (extend lease)
success/failure: running -> succeeded/failed
expired lease: running -> queued; attempt_count 达上限后 -> failed
```

`claim_next` 使用 `BEGIN IMMEDIATE` 包住 FIFO 查询与条件更新。多个进程同时竞争时，SQLite write lock 保证只有一个 worker 拿到指定 run。`finish(..., worker_id=...)` 校验 ownership，旧 worker 不能结束已经被其他 worker 重新领取的任务。

## 本地运行

终端 1：

```powershell
$env:DEMO_EXECUTION_MODE='worker'
$env:DEMO_RUN_STORE_PATH='reports/demo_runs/run_registry.sqlite3'
uv run python scripts/run_demo_server.py
```

终端 2：

```powershell
uv run python scripts/run_demo_worker.py
```

调试时只处理一个任务：

```powershell
uv run python scripts/run_demo_worker.py --once
```

关键配置：

| 环境变量 | 默认值 | 含义 |
|---|---:|---|
| `DEMO_EXECUTION_MODE` | `background` | `background` 或 `worker` |
| `DEMO_RUN_STORE_PATH` | `reports/demo_runs/run_registry.sqlite3` | API 与 worker 必须共享 |
| `DEMO_WORKER_LEASE_SECONDS` | 120 | worker 每 1/3 lease 周期续租 |
| `DEMO_WORKER_MAX_ATTEMPTS` | 3 | 租约过期后的最大领取次数 |
| `DEMO_WORKER_POLL_SECONDS` | 1 | 空队列轮询间隔 |

## Compose

`compose.yml` 现在包含 `app + worker + redis`。app 以 worker mode 启动，两个服务共享 `deepresearch_demo_runs` 和 `deepresearch_uploads` volumes：

```powershell
docker compose up --build
docker compose logs -f app worker
docker compose up --scale worker=3
```

当前开发机没有 Docker CLI，因此 Compose 只做了 YAML/配置和 API 级测试，未声称真实容器构建成功。

## 本地 E2E 证据

冻结报告：`reports/worker_eval/e2e_v1/report.md`。

真实流程为 FastAPI worker mode 入队 `demo_04a791cbcddd`，随后独立 Python 进程运行 `run_demo_worker.py --once`；状态从 queued 变为 succeeded，`worker_id=e2e-worker`、`attempt_count=1`，artifacts endpoint 返回 HTTP 200 和 5 条 Evidence。

## 已验证

- schema v1/v2/v3 自动迁移到 v4；
- run store 重开后 queued/running 状态仍存在；
- 多线程模拟多个 worker，领取结果不重复；
- FIFO、ownership heartbeat、lease extension；
- 第一次 lease expiry 重排，达到 max attempts 后失败；
- worker executor 成功/异常均持久化终态；
- FastAPI worker mode 返回 queued，独立 worker 后变为 succeeded。

## 生产边界

这是单机共享卷方案，不是完整分布式队列：

- SQLite 适合单机多进程，不适合跨主机共享文件系统高并发写入；
- 没有 dead-letter queue、优先级、公平调度、任务取消和 per-tenant quota；
- artifact 仍写本地 volume，不是对象存储；
- 更大规模应将队列换成 Redis Streams/RabbitMQ/Kafka，把 run state 放 Postgres，并保留 lease/heartbeat/idempotency 语义。
