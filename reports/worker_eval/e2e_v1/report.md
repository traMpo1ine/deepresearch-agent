# Durable Worker Local E2E

- Observed: `2026-07-17T02:22:57+08:00`
- Run: `demo_04a791cbcddd`
- Store schema: `v4`
- API execution mode: `worker`
- Initial state: `queued`
- Final state: `succeeded`
- Claimed by: `e2e-worker`
- Attempt count: `1`
- Artifacts endpoint: `HTTP 200`
- Evidence returned: `5`

## Path exercised

1. FastAPI `POST /api/runs` admitted and persisted the job without scheduling BackgroundTasks.
2. A separate `scripts/run_demo_worker.py --once` process opened the same SQLite file.
3. The worker used `claim_next` to move the run from queued to running with ownership and lease fields.
4. The worker generated a real offline showcase artifact pack and persisted succeeded.
5. FastAPI reopened the persisted state and returned structured artifacts with five evidence items.

This is a local process-level smoke test, not a Docker or cross-host test. Docker CLI was unavailable on the development machine.
