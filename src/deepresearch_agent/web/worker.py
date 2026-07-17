from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable

from deepresearch_agent.showcase import build_showcase
from deepresearch_agent.web.run_store import DemoRun, DemoRunStore


WORKER_LOGGER = logging.getLogger("deepresearch_agent.worker")
WORKER_LOGGER.setLevel(logging.INFO)
RunExecutor = Callable[[DemoRun], Awaitable[None]]


async def execute_demo_run(job: DemoRun) -> None:
    await build_showcase(
        question=job.question,
        output_dir=job.output_dir,
        llm_backend="mock",
        model=job.model,
        repair_rounds=job.repair_rounds,
        corpus_path=job.corpus_path,
        enable_web_search=job.enable_web_search,
        web_search_provider=job.web_search_provider,
        max_web_results=job.max_web_results,
        use_iterative_search=job.enable_web_search,
    )


class DemoRunWorker:
    """Single-slot durable worker; run multiple processes for horizontal concurrency."""

    def __init__(
        self,
        store: DemoRunStore,
        *,
        worker_id: str,
        executor: RunExecutor = execute_demo_run,
        lease_seconds: int = 120,
        max_attempts: int = 3,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        if not worker_id.strip():
            raise ValueError("worker_id must not be empty")
        if lease_seconds < 3:
            raise ValueError("lease_seconds must be at least 3")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        self.store = store
        self.worker_id = worker_id
        self.executor = executor
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts
        self.poll_interval_seconds = poll_interval_seconds

    async def run_once(self) -> DemoRun | None:
        recovery = self.store.recover_expired_leases(self.max_attempts)
        if recovery["requeued"] or recovery["failed"]:
            self._log("lease_recovery", **recovery)
        job = self.store.claim_next(self.worker_id, self.lease_seconds)
        if job is None:
            return None
        self._log("running", run_id=job.run_id, attempt_count=job.attempt_count)
        heartbeat = asyncio.create_task(self._heartbeat_loop(job.run_id))
        try:
            await self.executor(job)
        except Exception as exc:  # noqa: BLE001 - persist worker failure for the API.
            finished = self.store.finish(
                job.run_id,
                "failed",
                str(exc),
                worker_id=self.worker_id,
            )
            self._log(
                "failed",
                run_id=job.run_id,
                attempt_count=job.attempt_count,
                error_type=type(exc).__name__,
            )
        else:
            finished = self.store.finish(
                job.run_id,
                "succeeded",
                worker_id=self.worker_id,
            )
            self._log("succeeded", run_id=job.run_id, attempt_count=job.attempt_count)
        finally:
            heartbeat.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat
        return finished

    async def run_forever(self, stop_event: asyncio.Event | None = None) -> None:
        stop = stop_event or asyncio.Event()
        self._log(
            "started",
            lease_seconds=self.lease_seconds,
            max_attempts=self.max_attempts,
            poll_interval_seconds=self.poll_interval_seconds,
        )
        while not stop.is_set():
            processed = await self.run_once()
            if processed is None:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=self.poll_interval_seconds)
                except TimeoutError:
                    pass
        self._log("stopped")

    async def _heartbeat_loop(self, run_id: str) -> None:
        interval = min(max(self.lease_seconds / 3, 1.0), 30.0)
        while True:
            await asyncio.sleep(interval)
            if not self.store.heartbeat(run_id, self.worker_id, self.lease_seconds):
                raise RuntimeError(f"worker lost lease ownership for {run_id}")

    def _log(self, event: str, **fields: object) -> None:
        WORKER_LOGGER.info(
            json.dumps(
                {"event": f"demo_worker_{event}", "worker_id": self.worker_id, **fields},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )

