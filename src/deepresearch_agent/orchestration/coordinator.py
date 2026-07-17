from __future__ import annotations

import asyncio
import hashlib
import json
import time
import warnings
from pathlib import Path
from typing import Any

from deepresearch_agent.agents.base import AgentContext, BaseAgent
from deepresearch_agent.agents.critic import CriticAgent
from deepresearch_agent.agents.planner import PlannerAgent
from deepresearch_agent.agents.reader import ReaderAgent
from deepresearch_agent.agents.searcher import SearcherAgent
from deepresearch_agent.agents.verifier import VerifierAgent
from deepresearch_agent.agents.writer import WriterAgent
from deepresearch_agent.compression import TextRankCompressor
from deepresearch_agent.evidence_quality import (
    annotate_source_quality,
    suggest_follow_up_queries,
    summarize_source_quality,
)
from deepresearch_agent.llm import LLMBackendConfig, backend_status, create_llm_backend
from deepresearch_agent.memory import (
    NumpyVectorIndex,
    OpenAICompatibleEmbeddingProvider,
    SQLiteMemoryStore,
)
from deepresearch_agent.orchestration.dag import DAGTaskGraph
from deepresearch_agent.orchestration.state_machine import TaskStateMachine
from deepresearch_agent.redblue.blue_agent import BlueRepairAgent
from deepresearch_agent.schemas import (
    Claim,
    Evidence,
    RepairActionType,
    RepairLoopTrace,
    ResearchPlan,
    ResearchReport,
    ResearchTask,
    TaskStatus,
    TaskType,
    VerificationStatus,
)
from deepresearch_agent.schemas.core import new_id, utc_now
from deepresearch_agent.source_observability import summarize_live_sources
from deepresearch_agent.tools.web_search import web_search_status


class ResearchCoordinator:
    def __init__(
        self,
        max_concurrency: int = 4,
        memory_path: str | Path = "data/memory/deepresearch.sqlite3",
        vector_path: str | Path = "data/memory/vector_index.npz",
        plan_dir: str | Path = "reports/plans",
        repair_rounds: int = 2,
        use_memory_recall: bool = True,
        use_compression: bool = True,
        use_verifier: bool = True,
        use_redblue: bool = True,
        llm_backend: str = "mock",
        model: str | None = None,
        llm_timeout_seconds: float = 60.0,
        llm_max_retries: int = 2,
        llm_vllm_base_url: str = "http://localhost:8000/v1",
        planner_mode: str = "heuristic",
        min_evidence_count: int = 1,
        batch_replan_threshold: int = 1,
        corpus_path: str | Path = "data/corpus/offline_corpus.jsonl",
        use_iterative_search: bool = False,
        max_follow_up_queries: int = 1,
        source_quality_threshold: float = 0.58,
        enable_web_search: bool = False,
        web_search_provider: str = "disabled",
        max_web_results: int = 3,
        web_search_cache_path: str | Path | None = "data/memory/web_search_cache.sqlite3",
        web_search_cache_ttl_seconds: int = 3600,
        web_search_cache_backend: str = "sqlite",
        web_search_redis_url: str | None = None,
        embedding_provider: str = "hashing",
        embedding_base_url: str = "https://api.openai.com/v1",
        embedding_model: str = "text-embedding-3-small",
        embedding_api_key_env: str = "EMBEDDING_API_KEY",
        embedding_cache_path: str | Path = "data/memory/embedding_cache.sqlite3",
        embedding_timeout_seconds: float = 30.0,
        embedding_max_retries: int = 2,
        embedding_batch_size: int = 64,
        writer_mode: str = "template",
    ) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.state_machine = TaskStateMachine()
        self.memory = SQLiteMemoryStore(memory_path)
        self.vector_path = Path(vector_path)
        self.vector_index = self._load_vector_index(self.vector_path)
        self.plan_dir = Path(plan_dir)
        self.plan_dir.mkdir(parents=True, exist_ok=True)
        self.repair_rounds = repair_rounds
        self.use_memory_recall = use_memory_recall
        self.use_compression = use_compression
        self.use_verifier = use_verifier
        self.use_redblue = use_redblue
        self.llm_backend = llm_backend
        self.llm_timeout_seconds = llm_timeout_seconds
        self.llm_max_retries = llm_max_retries
        self.llm_vllm_base_url = llm_vllm_base_url
        self.min_evidence_count = min_evidence_count
        self.batch_replan_threshold = batch_replan_threshold
        self.corpus_path = str(corpus_path)
        self.use_iterative_search = use_iterative_search
        self.max_follow_up_queries = max_follow_up_queries
        self.source_quality_threshold = source_quality_threshold
        self.enable_web_search = enable_web_search
        self.web_search_provider = web_search_provider
        self.max_web_results = max_web_results
        self.web_search_cache_path = (
            str(web_search_cache_path) if web_search_cache_path is not None else None
        )
        self.web_search_cache_ttl_seconds = web_search_cache_ttl_seconds
        self.web_search_cache_backend = web_search_cache_backend
        self.web_search_redis_url = web_search_redis_url
        if embedding_provider not in {"hashing", "openai-compatible"}:
            raise ValueError("embedding_provider must be hashing or openai-compatible")
        self.embedding_provider_name = embedding_provider
        if writer_mode not in WriterAgent.MODES:
            raise ValueError(
                f"writer_mode must be one of: {', '.join(sorted(WriterAgent.MODES))}"
            )
        if writer_mode == "llm" and llm_backend == "mock":
            raise ValueError("writer_mode=llm requires a non-mock llm_backend")
        self.writer_mode = writer_mode
        self.embedding_adapter = (
            OpenAICompatibleEmbeddingProvider(
                base_url=embedding_base_url,
                model=embedding_model,
                api_key_env=embedding_api_key_env,
                cache_path=embedding_cache_path,
                timeout_seconds=embedding_timeout_seconds,
                max_retries=embedding_max_retries,
                batch_size=embedding_batch_size,
            )
            if embedding_provider == "openai-compatible"
            else None
        )
        self.llm_config = LLMBackendConfig(
            backend=llm_backend,
            model=model,
            timeout_seconds=llm_timeout_seconds,
            max_retries=llm_max_retries,
            vllm_base_url=llm_vllm_base_url,
        )
        self.llm_status = backend_status(self.llm_config)
        self.model = self.llm_status["model"]
        self.llm = create_llm_backend(self.llm_config)
        self.planner_mode = planner_mode
        self.planner = PlannerAgent(mode=planner_mode)
        self.searcher = SearcherAgent(
            corpus_path=corpus_path,
            enable_web_search=enable_web_search,
            web_search_provider=web_search_provider,
            max_web_results=max_web_results,
            web_search_cache_path=web_search_cache_path,
            web_search_cache_ttl_seconds=web_search_cache_ttl_seconds,
            web_search_cache_backend=web_search_cache_backend,
            web_search_redis_url=web_search_redis_url,
            embedding_provider=self.embedding_adapter,
        )
        self.reader = ReaderAgent()
        self.writer = WriterAgent(
            mode=writer_mode,
            llm_backend=self.llm if writer_mode == "llm" else None,
        )
        self.critic = CriticAgent()
        self.verifier = VerifierAgent()
        self.blue = BlueRepairAgent()
        self.compressor = TextRankCompressor()

    async def run(self, question: str) -> ResearchReport:
        run_id = new_id("run")
        started = utc_now()
        wall_started = time.perf_counter()
        self.memory.start_run(
            run_id,
            question,
            started.isoformat(),
            {
                "max_concurrency": self.semaphore._value,
                "use_memory_recall": self.use_memory_recall,
                "use_compression": self.use_compression,
                "use_verifier": self.use_verifier,
                "use_redblue": self.use_redblue,
                "llm_backend": self.llm_backend,
                "model": self.model,
                "llm_timeout_seconds": self.llm_timeout_seconds,
                "llm_max_retries": self.llm_max_retries,
                "llm_vllm_base_url": self.llm_vllm_base_url,
                "llm_status": self.llm_status,
                "planner_mode": self.planner_mode,
                "min_evidence_count": self.min_evidence_count,
                "batch_replan_threshold": self.batch_replan_threshold,
                "corpus_path": self.corpus_path,
                "use_iterative_search": self.use_iterative_search,
                "max_follow_up_queries": self.max_follow_up_queries,
                "source_quality_threshold": self.source_quality_threshold,
                "enable_web_search": self.enable_web_search,
                "web_search_provider": self.web_search_provider,
                "max_web_results": self.max_web_results,
                "web_search_cache_path": self.web_search_cache_path,
                "web_search_cache_ttl_seconds": self.web_search_cache_ttl_seconds,
                "web_search_cache_backend": self.web_search_cache_backend,
                "web_search_redis_configured": bool(self.web_search_redis_url),
                "web_search_status": web_search_status(self.web_search_provider),
                "embedding_status": self._embedding_telemetry(),
            },
        )
        plan_output = await self._run_agent(
            self.planner,
            question,
            run_id,
            {"stage": "planning", "planner_mode": self.planner_mode},
        )
        if not isinstance(plan_output, ResearchPlan):
            raise TypeError("PlannerAgent returned a non-ResearchPlan output.")
        plan = plan_output
        self._save_plan(run_id, plan.to_dict())
        self._save_plan_mermaid(run_id, plan.tasks)
        graph = DAGTaskGraph(plan.tasks)
        evidence: list[Evidence] = []
        context = None
        replan_count = 0
        batch_failure_events: list[dict[str, Any]] = []
        fallback_level = 0

        try:
            for batch in graph.topological_batches():
                executable: list[ResearchTask] = []
                for task in batch:
                    if not graph.dependencies_succeeded(task):
                        task.status = TaskStatus.BLOCKED
                        task.error = "At least one dependency did not succeed."
                        self.memory.add_task(run_id, task)
                        continue
                    self.state_machine.transition(task, TaskStatus.READY)
                    self.memory.add_task(run_id, task)
                    executable.append(task)
                batch_evidence = await asyncio.gather(
                    *(self._execute_task(run_id, task, graph) for task in executable)
                )
                for items in batch_evidence:
                    evidence.extend(items)
                failed_tasks = [
                    task for task in executable if task.status in {TaskStatus.FAILED, TaskStatus.TIMED_OUT}
                ]
                if len(failed_tasks) >= self.batch_replan_threshold:
                    replan_count += 1
                    event = {
                        "batch_task_ids": [task.id for task in executable],
                        "failed_task_ids": [task.id for task in failed_tasks],
                        "replan_index": replan_count,
                    }
                    batch_failure_events.append(event)
                    recovery_evidence = await self._run_recovery_tasks(run_id, failed_tasks)
                    evidence.extend(recovery_evidence)

            recalled = (
                self._recall_memory(question, existing_ids={item.id for item in evidence})
                if self.use_memory_recall
                else []
            )
            evidence.extend(recalled)
            evidence = self._dedupe_evidence(evidence)
            follow_up_queries: list[str] = []
            supplemental_evidence: list[Evidence] = []
            if self.use_iterative_search:
                follow_up_queries, supplemental_evidence = await self._run_iterative_follow_up(
                    run_id,
                    question,
                    evidence,
                )
                evidence.extend(supplemental_evidence)
                evidence = self._dedupe_evidence(evidence)
            if len(evidence) < self.min_evidence_count:
                fallback_level = 3
            context = self.compressor.compress_evidence(question, evidence) if self.use_compression else None
            report_output = await self._run_agent(
                self.writer,
                {
                    "question": question,
                    "evidence": evidence,
                    "context": context,
                    "plan_type": plan.plan_type,
                },
                run_id,
                {"stage": "writing", "evidence_count": len(evidence), "plan_type": plan.plan_type.value},
            )
            if not isinstance(report_output, ResearchReport):
                raise TypeError("WriterAgent returned a non-ResearchReport output.")
            report = report_output
            report.run_id = run_id
            if fallback_level:
                report.limitations.append(
                    "Fallback synthesis was used because retrieved evidence was below the configured threshold."
                )
            before_repair_weak = sum(1 for claim in report.claims if claim.needs_verification)
            if self.use_verifier:
                seen_fingerprints: set[str] = set()
                repeated_modify_targets: set[str] = set()
                repair_stop_reason = "MAX_ROUNDS"
                for round_index in range(self.repair_rounds):
                    fingerprint_before = self._claim_fingerprint(report)
                    seen_fingerprints.add(fingerprint_before)
                    actions_before = len(report.repair_actions)
                    weak_before = self._weak_claim_count(report)
                    verified_claims: list[Claim] = []
                    for claim in report.claims:
                        verified_output = await self._run_agent(
                            self.verifier,
                            {"claim": claim, "evidence": report.evidence},
                            run_id,
                            {"stage": "verification", "claim_id": claim.id},
                        )
                        if not isinstance(verified_output, Claim):
                            raise TypeError("VerifierAgent returned a non-Claim output.")
                        verified_claims.append(verified_output)
                    report.claims = verified_claims
                    if self.use_redblue:
                        findings_output = await self._run_agent(
                            self.critic,
                            report,
                            run_id,
                            {"stage": "red_review", "claim_count": len(report.claims)},
                        )
                        if not isinstance(findings_output, list):
                            raise TypeError("CriticAgent returned a non-list output.")
                        findings = findings_output
                    else:
                        findings = []
                    weak_after_verify = self._weak_claim_count(report)
                    if not findings:
                        report.repair_loop_trace.append(
                            RepairLoopTrace(
                                round_index=round_index,
                                finding_count=0,
                                weak_claim_count=weak_after_verify,
                                repair_action_count=len(report.repair_actions) - actions_before,
                                claim_fingerprint_before=fingerprint_before,
                                claim_fingerprint_after=self._claim_fingerprint(report),
                                converged=True,
                                stop_reason="CONVERGED",
                            )
                        )
                        repair_stop_reason = "CONVERGED"
                        break
                    repaired_output = await self._run_agent(
                        self.blue,
                        {"report": report, "findings": findings},
                        run_id,
                        {"stage": "blue_repair", "finding_count": len(findings)},
                    )
                    if not isinstance(repaired_output, ResearchReport):
                        raise TypeError("BlueRepairAgent returned a non-ResearchReport output.")
                    report = repaired_output
                    fingerprint_after = self._claim_fingerprint(report)
                    action_delta = report.repair_actions[actions_before:]
                    modified_targets = [
                        action.target_claim_id
                        for action in action_delta
                        if action.action_type == RepairActionType.MODIFY
                    ]
                    oscillating = fingerprint_after in seen_fingerprints or any(
                        target in repeated_modify_targets for target in modified_targets
                    )
                    repeated_modify_targets.update(modified_targets)
                    weak_after_repair = self._weak_claim_count(report)
                    severe_findings = any(finding.severity >= 4 for finding in findings)
                    converged = weak_after_repair >= weak_before and not severe_findings
                    stop_reason = (
                        "OSCILLATION"
                        if oscillating
                        else "CONVERGED"
                        if converged
                        else "MAX_ROUNDS"
                        if round_index == self.repair_rounds - 1
                        else ""
                    )
                    report.repair_loop_trace.append(
                        RepairLoopTrace(
                            round_index=round_index,
                            finding_count=len(findings),
                            weak_claim_count=weak_after_repair,
                            repair_action_count=len(action_delta),
                            claim_fingerprint_before=fingerprint_before,
                            claim_fingerprint_after=fingerprint_after,
                            converged=converged,
                            oscillating=oscillating,
                            stop_reason=stop_reason,
                        )
                    )
                    if oscillating or converged:
                        repair_stop_reason = stop_reason
                        break
                else:
                    repair_stop_reason = "MAX_ROUNDS"
                if report.repair_loop_trace and not report.repair_loop_trace[-1].stop_reason:
                    report.repair_loop_trace[-1].stop_reason = repair_stop_reason
            report.run_summary = self._build_run_summary(
                run_id=run_id,
                tasks=plan.tasks,
                evidence=evidence,
                report=report,
                started=wall_started,
                compression_ratio=context.compression_ratio if context else 1.0,
                recalled_count=len(recalled),
                before_repair_weak=before_repair_weak,
                fallback_level=fallback_level,
                replan_count=replan_count,
                batch_failure_events=batch_failure_events,
                follow_up_queries=follow_up_queries,
                supplemental_evidence_count=len(supplemental_evidence),
            )
            for claim in report.claims:
                self.memory.add_claim(run_id, claim)
            for action in report.repair_actions:
                self.memory.add_repair_action(run_id, action)
            self.memory.add_report(report)
            self.memory.update_run_metadata(run_id, report.run_summary)
            self.memory.finish_run(run_id, utc_now().isoformat(), "succeeded")
            self.vector_index.save(self.vector_path)
            return report
        except Exception:
            self.memory.finish_run(run_id, utc_now().isoformat(), "failed")
            raise

    def _load_vector_index(self, path: Path) -> NumpyVectorIndex:
        if not path.exists():
            return NumpyVectorIndex(dim=64)
        try:
            return NumpyVectorIndex.load(path)
        except Exception as exc:  # noqa: BLE001 - corrupted runtime artifact should not break fresh runs.
            warnings.warn(
                f"Could not load vector index at {path}; rebuilding an empty index. Error: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            return NumpyVectorIndex(dim=64)

    def _dedupe_evidence(self, evidence: list[Evidence]) -> list[Evidence]:
        by_key: dict[tuple[str, str], Evidence] = {}
        for item in evidence:
            annotate_source_quality(item)
            key = (item.source_id, item.quote or item.text)
            if key not in by_key or item.score > by_key[key].score:
                by_key[key] = item
        return sorted(by_key.values(), key=lambda item: item.score, reverse=True)

    async def _run_agent(
        self,
        agent: BaseAgent,
        agent_input: object,
        run_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> object:
        result = await agent.run(agent_input, AgentContext(run_id=run_id, metadata=metadata or {}))
        self.memory.add_agent_event(
            run_id,
            result.agent_name,
            result.ok,
            result.latency_seconds,
            result.error,
            result.metadata,
        )
        if not result.ok:
            raise RuntimeError(result.error or f"{result.agent_name} failed without an error message.")
        return result.output

    async def _execute_task(
        self,
        run_id: str,
        task: ResearchTask,
        graph: DAGTaskGraph | None,
    ) -> list[Evidence]:
        async with self.semaphore:
            for attempt in range(task.max_retries + 1):
                try:
                    task.retry_count = attempt
                    self.state_machine.transition(task, TaskStatus.RUNNING)
                    started = time.perf_counter()
                    if task.task_type in {TaskType.ROOT, TaskType.SYNTHESIZE, TaskType.VERIFY, TaskType.REPAIR}:
                        evidence: list[Evidence] = []
                    else:
                        evidence = await asyncio.wait_for(
                            self._search_and_read(run_id, task),
                            timeout=task.timeout_seconds,
                        )
                    self.state_machine.transition(task, TaskStatus.SUCCEEDED)
                    self.state_machine.transition(task, TaskStatus.VERIFIED)
                    self.memory.add_task(run_id, task)
                    self.memory.add_agent_event(
                        run_id,
                        "coordinator",
                        True,
                        time.perf_counter() - started,
                        None,
                        {"task_id": task.id, "task_type": task.task_type.value, "attempt": attempt},
                    )
                    for item in evidence:
                        self.memory.add_evidence(item, run_id=run_id)
                        self.vector_index.add(item.id, f"{item.title} {item.text} {item.quote or ''}")
                    return evidence
                except Exception as exc:  # noqa: BLE001 - recorded in task state and memory.
                    timed_out = isinstance(exc, TimeoutError | asyncio.TimeoutError)
                    task.error = str(exc)
                    if task.status == TaskStatus.RUNNING:
                        if timed_out:
                            task.error = f"Task timed out after {task.timeout_seconds} seconds."
                            self.state_machine.transition(task, TaskStatus.TIMED_OUT)
                        else:
                            self.state_machine.transition(task, TaskStatus.FAILED)
                    self.memory.add_task(run_id, task)
                    self.memory.add_agent_event(
                        run_id,
                        "coordinator",
                        False,
                        0.0,
                        str(exc),
                        {"task_id": task.id, "attempt": attempt},
                    )
                    if attempt < task.max_retries:
                        self.state_machine.transition(task, TaskStatus.READY)
                        continue
                    if task.status == TaskStatus.TIMED_OUT:
                        self.state_machine.transition(task, TaskStatus.FAILED)
                        self.memory.add_task(run_id, task)
                    return []

    async def _search_and_read(self, run_id: str, task: ResearchTask) -> list[Evidence]:
        search_output = await self._run_agent(
            self.searcher,
            task,
            run_id,
            {"stage": "search", "task_id": task.id, "task_type": task.task_type.value},
        )
        if not isinstance(search_output, list):
            raise TypeError("SearcherAgent returned a non-list output.")
        read_output = await self._run_agent(
            self.reader,
            {"task": task, "results": search_output},
            run_id,
            {"stage": "read", "task_id": task.id, "search_result_count": len(search_output)},
        )
        if not isinstance(read_output, list):
            raise TypeError("ReaderAgent returned a non-list output.")
        return read_output

    async def _run_recovery_tasks(
        self,
        run_id: str,
        failed_tasks: list[ResearchTask],
    ) -> list[Evidence]:
        recovered: list[Evidence] = []
        for failed_task in failed_tasks:
            recovery_task = ResearchTask(
                question=f"Recovery search for failed task: {failed_task.question}",
                task_type=TaskType.SEARCH,
                parent_id=failed_task.parent_id,
                dependencies=list(failed_task.dependencies),
                priority=failed_task.priority + 100,
                expected_evidence=f"Fallback evidence for: {failed_task.question}",
                max_retries=0,
                timeout_seconds=max(failed_task.timeout_seconds, 5.0),
            )
            self.memory.add_task(run_id, recovery_task)
            items = await self._execute_task(run_id, recovery_task, graph=None)
            if items:
                recovered.extend(items)
                self._mark_task_recovered(run_id, failed_task, recovery_task.id)
        return recovered

    async def _run_iterative_follow_up(
        self,
        run_id: str,
        question: str,
        evidence: list[Evidence],
    ) -> tuple[list[str], list[Evidence]]:
        queries = suggest_follow_up_queries(
            question,
            evidence,
            quality_threshold=self.source_quality_threshold,
            max_queries=self.max_follow_up_queries,
        )
        if not queries:
            return [], []
        supplemental: list[Evidence] = []
        existing_keys = {(item.source_id, item.quote or item.text) for item in evidence}
        for index, query in enumerate(queries[: self.max_follow_up_queries], start=1):
            task = ResearchTask(
                question=query,
                task_type=TaskType.SEARCH,
                priority=250 + index,
                expected_evidence="Supplemental evidence for low-quality or quote-sparse first pass.",
                max_retries=0,
                timeout_seconds=self.llm_timeout_seconds,
            )
            self.memory.add_task(run_id, task)
            items = await self._execute_task(run_id, task, graph=None)
            for item in items:
                key = (item.source_id, item.quote or item.text)
                if key in existing_keys:
                    continue
                existing_keys.add(key)
                item.metadata["iterative_search"] = True
                item.metadata["follow_up_query"] = query
                item.metadata["follow_up_index"] = index
                annotate_source_quality(item)
                self.memory.add_evidence(item, run_id=run_id)
                supplemental.append(item)
        return queries, supplemental

    def _mark_task_recovered(self, run_id: str, task: ResearchTask, recovery_task_id: str) -> None:
        try:
            self.state_machine.transition(task, TaskStatus.READY)
            self.state_machine.transition(task, TaskStatus.RUNNING)
            self.state_machine.transition(task, TaskStatus.SUCCEEDED)
            self.state_machine.transition(task, TaskStatus.VERIFIED)
        except Exception:  # noqa: BLE001 - recovery trace should not hide recovered evidence.
            task.status = TaskStatus.VERIFIED
        task.error = f"Recovered by lightweight replan task {recovery_task_id}."
        self.memory.add_task(run_id, task)

    def _recall_memory(self, question: str, existing_ids: set[str]) -> list[Evidence]:
        recalled: list[Evidence] = []
        for evidence_id, _score in self.vector_index.search(question, top_k=5):
            if evidence_id in existing_ids:
                continue
            item = self.memory.get_evidence(evidence_id)
            if item:
                recalled.append(item)
        for item in self.memory.search_evidence_text(question, limit=5):
            if item.id not in existing_ids and item.id not in {ev.id for ev in recalled}:
                recalled.append(item)
        return recalled[:5]

    def _save_plan(self, run_id: str, payload: dict) -> None:
        path = self.plan_dir / f"{run_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_plan_mermaid(self, run_id: str, tasks: list[ResearchTask]) -> None:
        labels = {}
        for task in tasks:
            question = task.question[:42].replace('"', "")
            labels[task.id] = f"{task.task_type.value}: {question}"
        lines = ["flowchart TD"]
        for task in tasks:
            lines.append(f'    {task.id}["{labels[task.id]}"]')
        for task in tasks:
            for dep_id in task.dependencies:
                lines.append(f"    {dep_id} --> {task.id}")
        (self.plan_dir / f"{run_id}.mmd").write_text("\n".join(lines), encoding="utf-8")

    def _embedding_telemetry(self) -> dict[str, object]:
        telemetry_reader = getattr(self.searcher, "embedding_telemetry", None)
        if callable(telemetry_reader):
            return telemetry_reader()
        return {
            "provider": "unknown",
            "available": False,
            "reason": "searcher does not expose embedding telemetry",
        }

    def _build_run_summary(
        self,
        run_id: str,
        tasks: list[ResearchTask],
        evidence: list[Evidence],
        report: ResearchReport,
        started: float,
        compression_ratio: float,
        recalled_count: int,
        before_repair_weak: int,
        fallback_level: int,
        replan_count: int,
        batch_failure_events: list[dict[str, Any]],
        follow_up_queries: list[str],
        supplemental_evidence_count: int,
    ) -> dict:
        events = self.memory.list_agent_events(run_id)
        after_repair_weak = sum(1 for claim in report.claims if claim.needs_verification)
        repair_rounds_used = len(report.repair_loop_trace)
        source_quality = summarize_source_quality(evidence).to_dict()
        live_sources = summarize_live_sources(evidence).to_dict()
        telemetry_reader = getattr(self.searcher, "web_search_telemetry", None)
        web_search_telemetry = (
            telemetry_reader()
            if callable(telemetry_reader)
            else {
                "summary": {
                    "event_count": 0,
                    "status_counts": {},
                    "provider_counts": {},
                    "operational_rate": 0.0,
                    "total_retries": 0,
                    "mean_latency_seconds": 0.0,
                    "max_latency_seconds": 0.0,
                    "circuit_open_count": 0,
                },
                "events": [],
            }
        )
        repair_stop_reason = (
            report.repair_loop_trace[-1].stop_reason if report.repair_loop_trace else "NOT_RUN"
        )
        timed_out_tasks = sum(
            1
            for task in tasks
            if task.status == TaskStatus.TIMED_OUT
            or "timed out" in (task.error or "").lower()
        )
        failed_tasks = sum(1 for task in tasks if task.status == TaskStatus.FAILED)
        retry_count = sum(task.retry_count for task in tasks)
        return {
            "run_id": run_id,
            "total_latency_seconds": time.perf_counter() - started,
            "task_count": len(tasks),
            "succeeded_tasks": sum(1 for task in tasks if task.status in {TaskStatus.SUCCEEDED, TaskStatus.VERIFIED}),
            "failed_tasks": failed_tasks,
            "timed_out_tasks": timed_out_tasks,
            "blocked_tasks": sum(1 for task in tasks if task.status == TaskStatus.BLOCKED),
            "retry_count": retry_count,
            "timeout_recovery_rate": (
                max(timed_out_tasks - failed_tasks, 0) / timed_out_tasks if timed_out_tasks else 0.0
            ),
            "batch_replan_success_rate": (
                1.0 if replan_count and not batch_failure_events[-1].get("unrecovered", False) else 0.0
            ),
            "fallback_report_rate": 1.0 if fallback_level == 3 else 0.0,
            "evidence_count": len(evidence),
            "recalled_evidence_count": recalled_count,
            "repair_count": len(report.repair_actions),
            "repair_success_rate": (
                max(before_repair_weak - after_repair_weak, 0) / before_repair_weak
                if before_repair_weak
                else 1.0
            ),
            "compression_ratio": compression_ratio,
            "avg_task_latency": (
                sum(event["latency_seconds"] for event in events) / len(events) if events else 0.0
            ),
            "fallback_level": fallback_level,
            "replan_count": replan_count,
            "batch_failure_events": batch_failure_events,
            "iterative_search_enabled": self.use_iterative_search,
            "follow_up_queries": follow_up_queries,
            "follow_up_query_count": len(follow_up_queries),
            "supplemental_evidence_count": supplemental_evidence_count,
            "source_quality": source_quality,
            "live_sources": live_sources,
            "web_search_telemetry": web_search_telemetry,
            "embedding_telemetry": self._embedding_telemetry(),
            "repair_rounds_used": repair_rounds_used,
            "repair_converged": any(trace.converged for trace in report.repair_loop_trace),
            "repair_oscillation_detected": any(
                trace.oscillating for trace in report.repair_loop_trace
            ),
            "repair_stop_reason": repair_stop_reason,
            "llm_backend": self.llm_backend,
            "model": self.model,
            "llm_timeout_seconds": self.llm_timeout_seconds,
            "llm_max_retries": self.llm_max_retries,
            "llm_vllm_base_url": self.llm_vllm_base_url,
            "llm_status": self.llm_status,
            "writer_mode": self.writer_mode,
            "writer_generation": self.writer.last_generation,
            "llm_usage": getattr(self.llm, "last_usage", {}),
            "llm_total_cost_estimate": getattr(self.llm, "total_cost_estimate", 0.0),
            "planner_mode": self.planner_mode,
            "corpus_path": self.corpus_path,
            "source_quality_threshold": self.source_quality_threshold,
            "enable_web_search": self.enable_web_search,
            "web_search_provider": self.web_search_provider,
            "max_web_results": self.max_web_results,
            "web_search_cache_path": self.web_search_cache_path,
            "web_search_cache_ttl_seconds": self.web_search_cache_ttl_seconds,
            "web_search_cache_backend": self.web_search_cache_backend,
            "web_search_redis_configured": bool(self.web_search_redis_url),
            "web_search_status": web_search_status(self.web_search_provider),
        }

    def _weak_claim_count(self, report: ResearchReport) -> int:
        return sum(
            1
            for claim in report.claims
            if claim.needs_verification
            or claim.verification_status
            in {
                VerificationStatus.UNKNOWN,
                VerificationStatus.UNSUPPORTED,
                VerificationStatus.CONTRADICTED,
                VerificationStatus.PARTIAL,
            }
        )

    def _claim_fingerprint(self, report: ResearchReport) -> str:
        payload = [
            {
                "id": claim.id,
                "text": claim.text,
                "status": claim.verification_status.value,
                "citations": claim.citation_ids,
            }
            for claim in report.claims
        ]
        return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
