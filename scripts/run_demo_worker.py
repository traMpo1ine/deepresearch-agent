from __future__ import annotations

import argparse
import asyncio
import logging
import os
import socket
from pathlib import Path
from uuid import uuid4

from deepresearch_agent.web.run_store import DemoRunStore
from deepresearch_agent.web.worker import DemoRunWorker


async def _run(args: argparse.Namespace) -> None:
    store = DemoRunStore(args.run_store_path)
    worker = DemoRunWorker(
        store,
        worker_id=args.worker_id,
        lease_seconds=args.lease_seconds,
        max_attempts=args.max_attempts,
        poll_interval_seconds=args.poll_interval_seconds,
    )
    if args.once:
        await worker.run_once()
        return
    await worker.run_forever()


def main() -> int:
    default_worker_id = f"{socket.gethostname()}-{os.getpid()}-{uuid4().hex[:8]}"
    parser = argparse.ArgumentParser(description="Run the durable DeepResearch demo worker.")
    parser.add_argument(
        "--run-store-path",
        type=Path,
        default=Path(os.getenv("DEMO_RUN_STORE_PATH", "reports/demo_runs/run_registry.sqlite3")),
    )
    parser.add_argument("--worker-id", default=default_worker_id)
    parser.add_argument(
        "--lease-seconds",
        type=int,
        default=int(os.getenv("DEMO_WORKER_LEASE_SECONDS", "120")),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=int(os.getenv("DEMO_WORKER_MAX_ATTEMPTS", "3")),
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=float(os.getenv("DEMO_WORKER_POLL_SECONDS", "1")),
    )
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

