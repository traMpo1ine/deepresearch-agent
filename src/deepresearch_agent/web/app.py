from __future__ import annotations

import json
import hashlib
import logging
import os
import re
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from deepresearch_agent.corpus_profiles import (
    ensure_profile_built,
    list_corpus_profiles,
)
from deepresearch_agent.llm import LLMBackendConfig, LLMMessage, backend_status, create_llm_backend
from deepresearch_agent.showcase import build_showcase
from deepresearch_agent.tools.web_search import web_search_status
from deepresearch_agent.web.metrics import ServiceMetrics
from deepresearch_agent.web.run_store import (
    DemoRun,
    DemoRunStore,
    IdempotencyConflictError,
    RunCapacityError,
)
from deepresearch_agent.web.upload_store import (
    UploadedCorpusStore,
    UploadTooLargeError,
    UploadValidationError,
)

try:
    from fastapi import (
        BackgroundTasks,
        FastAPI,
        File,
        HTTPException,
        Query,
        Request,
        Response,
        UploadFile,
    )
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised by users without the web extra.
    raise RuntimeError(
        "The web demo requires FastAPI. Install with `uv sync --extra web --extra dev`."
    ) from exc


ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_SHOWCASE_CANDIDATES = (
    ROOT / "reports" / "golden_demo" / "deepseek_v3",
    ROOT / "reports" / "final" / "final_sprint_check" / "showcase",
    ROOT / "reports" / "showcase" / "final_check",
)
DEFAULT_SHOWCASE_REQUIRED_FILES = (
    "plan.md",
    "report.md",
    "report.json",
    "run_summary.json",
)
DEMO_RUNS_DIR = ROOT / "reports" / "demo_runs"
UPLOAD_ROOT = ROOT / "data" / "uploads"
ACCESS_LOGGER = logging.getLogger("deepresearch_agent.access")
ACCESS_LOGGER.setLevel(logging.INFO)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class RunRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    backend: str = "mock"
    model: str | None = None
    repair_rounds: int = Field(default=2, ge=0, le=5)
    corpus_profile: str = "offline_agent_docs"
    uploaded_corpus_id: str | None = None
    enable_web_search: bool = False
    web_search_provider: str = "wikipedia,arxiv"
    max_web_results: int = Field(default=4, ge=1, le=8)


class DeepSeekShowcaseRequest(BaseModel):
    run_real: bool = False
    question: str = "为什么 DeepResearch Agent 需要引用验证和 Red-Blue 修复？"
    model: str = "deepseek-v4-flash"
    max_tokens: int = Field(default=512, ge=64, le=2048)


def create_app(
    run_store_path: str | Path | None = None,
    stale_run_after_seconds: int = 3600,
    max_active_runs: int | None = None,
    upload_root: str | Path | None = None,
    max_upload_bytes: int | None = None,
    execution_mode: str | None = None,
) -> FastAPI:
    started_at = time.perf_counter()
    resolved_execution_mode = execution_mode or os.getenv("DEMO_EXECUTION_MODE", "background")
    if resolved_execution_mode not in {"background", "worker"}:
        raise ValueError("DEMO_EXECUTION_MODE must be background or worker")
    active_capacity = max(1, max_active_runs or _positive_int_env("DEMO_MAX_ACTIVE_RUNS", 2))
    resolved_run_store_path = (
        run_store_path
        or os.getenv("DEMO_RUN_STORE_PATH")
        or DEMO_RUNS_DIR / "run_registry.sqlite3"
    )
    run_store = DemoRunStore(resolved_run_store_path)
    recovered_stale_runs = (
        run_store.recover_stale(stale_run_after_seconds)
        if resolved_execution_mode == "background"
        else 0
    )
    service_metrics = ServiceMetrics()
    upload_store = UploadedCorpusStore(
        upload_root or UPLOAD_ROOT,
        max_bytes=max_upload_bytes or _positive_int_env("DEMO_MAX_UPLOAD_BYTES", 10 * 1024 * 1024),
    )
    app = FastAPI(
        title="DeepResearch Agent Demo",
        description="Local FastAPI demo for the offline DeepResearch Agent showcase.",
        version="0.1.0",
    )
    app.state.run_store = run_store
    app.state.service_metrics = service_metrics
    app.state.upload_store = upload_store

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.middleware("http")
    async def request_observability(request: Request, call_next):
        request_id = _request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_seconds = time.perf_counter() - started
            service_metrics.observe_http(
                request.method,
                _route_template(request),
                status_code,
                duration_seconds,
            )
            ACCESS_LOGGER.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": round(duration_seconds * 1000, 3),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        content = service_metrics.render(
            uptime_seconds=time.perf_counter() - started_at,
            run_status_counts=run_store.status_counts(),
            max_active_runs=active_capacity,
        )
        return Response(content=content, media_type="text/plain; version=0.0.4")

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        status = backend_status(LLMBackendConfig(backend="deepseek"))
        return {
            "ok": True,
            "app": "deepresearch-agent-demo",
            "version": "0.1.0",
            "uptime_seconds": round(time.perf_counter() - started_at, 3),
            "default_backend": "mock",
            "deepseek_env_configured": status["env_configured"],
            "deepseek_model": status["model"],
            "corpus_profiles": [_profile_payload(profile) for profile in list_corpus_profiles()],
            "web_search": web_search_status("url,wikipedia,arxiv,github,tavily,searxng"),
            "run_store": {
                "backend": "sqlite_wal",
                "path": _display_path(run_store.path),
                "status_counts": run_store.status_counts(),
                "recovered_stale_runs": recovered_stale_runs,
                "max_active_runs": active_capacity,
                "execution_mode": resolved_execution_mode,
            },
            "uploads": {
                "enabled": True,
                "max_bytes": upload_store.max_bytes,
                "accepted_formats": ["pdf", "md", "txt", "html"],
                "corpus_count": len(upload_store.list()),
            },
            "boundary": "Generation stays mock by default; users may explicitly enable real external data.",
        }

    @app.get("/api/health/live")
    async def liveness() -> dict[str, Any]:
        return {
            "ok": True,
            "status": "alive",
            "uptime_seconds": round(time.perf_counter() - started_at, 3),
        }

    @app.get("/api/health/ready")
    async def readiness() -> dict[str, Any]:
        checks = {
            "static_assets": STATIC_DIR.is_dir() and (STATIC_DIR / "index.html").is_file(),
            "corpus_profiles": bool(list_corpus_profiles()),
            "reports_directory_parent": DEMO_RUNS_DIR.parent.is_dir(),
            "run_store": run_store.is_ready(),
            "upload_store": upload_store.is_ready(),
        }
        if not all(checks.values()):
            raise HTTPException(
                status_code=503,
                detail={"ok": False, "status": "not_ready", "checks": checks},
            )
        return {"ok": True, "status": "ready", "checks": checks}

    @app.get("/api/corpus-profiles")
    async def corpus_profiles() -> dict[str, Any]:
        return {
            "profiles": [_profile_payload(profile) for profile in list_corpus_profiles()],
            "uploads": [item.to_dict() for item in upload_store.list()],
        }

    @app.post("/api/corpora/uploads", status_code=201)
    async def upload_corpus(response: Response, file: UploadFile = File(...)) -> dict[str, Any]:
        try:
            item, created = await upload_store.ingest(file.filename, file)
        except UploadTooLargeError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except UploadValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            await file.close()
        if not created:
            response.status_code = 200
        return {**item.to_dict(), "deduplicated": not created}

    @app.get("/api/corpora/uploads")
    async def list_uploaded_corpora(
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, Any]:
        return {"uploads": [item.to_dict() for item in upload_store.list(limit)]}

    @app.get("/api/corpora/uploads/{corpus_id}")
    async def get_uploaded_corpus(corpus_id: str) -> dict[str, Any]:
        item = upload_store.get(corpus_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Unknown uploaded corpus: {corpus_id}")
        return item.to_dict()

    @app.get("/api/showcase/default")
    async def default_showcase() -> dict[str, Any]:
        showcase_dir = _find_default_showcase()
        if showcase_dir is None:
            candidates = [_display_path(path) for path in DEFAULT_SHOWCASE_CANDIDATES]
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "No default showcase artifacts were found.",
                    "candidates": candidates,
                    "hint": 'Run `uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？" --output-dir reports/showcase/final_check`.',
                },
            )
        return _load_showcase_payload(showcase_dir, source="default")

    @app.post("/api/runs", status_code=202)
    async def start_run(
        payload: RunRequest,
        request: Request,
        response: Response,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        if payload.backend != "mock":
            raise HTTPException(
                status_code=400,
                detail="Demo runs only allow backend='mock'. Use /api/deepseek-showcase for provider smoke.",
            )
        if payload.uploaded_corpus_id:
            uploaded = upload_store.get(payload.uploaded_corpus_id)
            if uploaded is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Unknown uploaded corpus: {payload.uploaded_corpus_id}",
                )
            corpus_path = Path(uploaded.corpus_path)
            selected_corpus_profile = f"upload:{uploaded.corpus_id}"
        else:
            try:
                corpus_path = ensure_profile_built(payload.corpus_profile)
            except KeyError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            selected_corpus_profile = payload.corpus_profile
        allowed_providers = {"url", "tavily", "wikipedia", "arxiv", "github", "searxng"}
        requested_providers = {
            item.strip().lower() for item in payload.web_search_provider.split(",") if item.strip()
        }
        if not requested_providers or not requested_providers <= allowed_providers:
            raise HTTPException(status_code=400, detail="Unsupported web search provider selection.")
        run_id = f"demo_{uuid4().hex[:12]}"
        output_dir = DEMO_RUNS_DIR / run_id
        job = DemoRun(
            run_id=run_id,
            question=payload.question,
            backend=payload.backend,
            model=payload.model,
            repair_rounds=payload.repair_rounds,
            corpus_profile=selected_corpus_profile,
            corpus_path=corpus_path,
            output_dir=output_dir,
            enable_web_search=payload.enable_web_search,
            web_search_provider=",".join(
                item.strip().lower()
                for item in payload.web_search_provider.split(",")
                if item.strip().lower() in allowed_providers
            ),
            max_web_results=payload.max_web_results,
            request_id=request.state.request_id,
            idempotency_key=_idempotency_key(request.headers.get("Idempotency-Key")),
            request_fingerprint=_request_fingerprint(payload),
        )
        try:
            admitted_job, created = run_store.admit(job, max_active_runs=active_capacity)
        except IdempotencyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RunCapacityError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
                headers={"Retry-After": "5"},
            ) from exc
        if not created:
            response.status_code = 200
            response.headers["X-Idempotent-Replay"] = "true"
            return _job_payload(admitted_job)
        if resolved_execution_mode == "background":
            background_tasks.add_task(_run_showcase_job, job.run_id, run_store)
        return _job_payload(job)

    @app.get("/api/runs")
    async def list_runs(
        limit: int = Query(default=20, ge=1, le=100),
        status: str | None = None,
    ) -> dict[str, Any]:
        try:
            runs = run_store.list_recent(limit=limit, status=status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "runs": [_job_payload(run) for run in runs],
            "status_counts": run_store.status_counts(),
        }

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str) -> dict[str, Any]:
        return _job_payload(_get_job(run_store, run_id))

    @app.get("/api/runs/{run_id}/artifacts")
    async def get_run_artifacts(run_id: str) -> dict[str, Any]:
        job = _get_job(run_store, run_id)
        if job.status != "succeeded":
            raise HTTPException(
                status_code=409,
                detail={"message": "Run artifacts are not ready.", "status": job.status},
            )
        return _load_showcase_payload(job.output_dir, source="demo_run")

    @app.post("/api/deepseek-showcase")
    async def deepseek_showcase(request: DeepSeekShowcaseRequest) -> dict[str, Any]:
        status = backend_status(
            LLMBackendConfig(
                backend="deepseek",
                model=request.model,
                max_tokens=request.max_tokens,
                max_retries=1,
            )
        )
        payload: dict[str, Any] = {
            "backend_status": status,
            "run_real": request.run_real,
            "success": False,
            "answer": "",
            "answer_preview": "",
            "token_usage": {},
            "estimated_cost_rmb": 0.0,
            "error": None,
            "boundary": "Provider smoke only; this output is not part of offline/mock benchmark metrics.",
        }
        if not request.run_real:
            payload["error"] = "Dry run only. Set run_real=true to call DeepSeek."
            return payload
        if not status["env_configured"]:
            payload["error"] = "DEEPSEEK_API_KEY is not configured."
            return payload
        try:
            backend = create_llm_backend(
                LLMBackendConfig(
                    backend="deepseek",
                    model=request.model,
                    max_tokens=request.max_tokens,
                    max_retries=1,
                )
            )
            answer = await backend.complete(_deepseek_messages(request.question))
            usage = getattr(backend, "last_usage", {})
            cost_usd = float(usage.get("cost_estimate_usd", 0.0) or 0.0)
            payload.update(
                {
                    "success": True,
                    "answer": answer,
                    "answer_preview": answer[:500],
                    "token_usage": usage,
                    "estimated_cost_rmb": round(cost_usd * 7.25, 8),
                }
            )
        except Exception as exc:  # noqa: BLE001 - provider smoke should report errors.
            payload["error"] = str(exc)
        return payload

    return app


async def _run_showcase_job(run_id: str, run_store: DemoRunStore) -> None:
    job = run_store.claim(run_id, worker_id="fastapi-background")
    if job is None:
        return
    _log_job_event(job, "running")
    try:
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
    except Exception as exc:  # noqa: BLE001 - background job state should preserve failures.
        job = run_store.finish(
            run_id,
            "failed",
            str(exc),
            worker_id="fastapi-background",
        )
        _log_job_event(job, "failed", error_type=type(exc).__name__)
    else:
        job = run_store.finish(run_id, "succeeded", worker_id="fastapi-background")
        _log_job_event(job, "succeeded")


def _get_job(run_store: DemoRunStore, run_id: str) -> DemoRun:
    job = run_store.get(run_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown demo run: {run_id}")
    return job


def _job_payload(job: DemoRun) -> dict[str, Any]:
    return {
        "run_id": job.run_id,
        "question": job.question,
        "backend": job.backend,
        "model": job.model,
        "repair_rounds": job.repair_rounds,
        "corpus_profile": job.corpus_profile,
        "corpus_path": _display_path(job.corpus_path),
        "output_dir": _display_path(job.output_dir),
        "enable_web_search": job.enable_web_search,
        "web_search_provider": job.web_search_provider,
        "max_web_results": job.max_web_results,
        "request_id": job.request_id,
        "worker_id": job.worker_id,
        "lease_expires_at": job.lease_expires_at,
        "attempt_count": job.attempt_count,
        "status": job.status,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "artifact_paths": _artifact_paths(job.output_dir),
    }


def _request_id(candidate: str | None) -> str:
    if candidate and REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return f"req_{uuid4().hex}"


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path) if isinstance(path, str) and path.startswith("/") else "/__unmatched__"


def _idempotency_key(candidate: str | None) -> str | None:
    if candidate is None:
        return None
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(candidate):
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must be 1-128 safe ASCII characters.",
        )
    return candidate


def _positive_int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _request_fingerprint(payload: RunRequest) -> str:
    canonical = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _log_job_event(job: DemoRun, status: str, error_type: str | None = None) -> None:
    ACCESS_LOGGER.info(
        json.dumps(
            {
                "event": "demo_run_status",
                "request_id": job.request_id,
                "run_id": job.run_id,
                "status": status,
                "error_type": error_type,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def _find_default_showcase() -> Path | None:
    for candidate in DEFAULT_SHOWCASE_CANDIDATES:
        if all((candidate / name).is_file() for name in DEFAULT_SHOWCASE_REQUIRED_FILES):
            return candidate
    return None


def _load_showcase_payload(showcase_dir: Path, source: str) -> dict[str, Any]:
    report_json = _read_json(showcase_dir / "report.json")
    run_summary = _read_json(showcase_dir / "run_summary.json")
    plan_md = _read_text(showcase_dir / "plan.md")
    report_md = _read_text(showcase_dir / "report.md")
    return {
        "source": source,
        "showcase_dir": _display_path(showcase_dir),
        "overview": _overview(report_json, run_summary),
        "plan": {
            "markdown": plan_md,
            "mermaid": _extract_mermaid(plan_md),
            "tasks": _extract_plan_tasks(plan_md),
        },
        "report": {
            "markdown": report_md,
            "title": report_json.get("title"),
            "summary": report_json.get("summary"),
            "claims": report_json.get("claims", []),
            "sections": report_json.get("sections", []),
            "limitations": report_json.get("limitations", []),
        },
        "evidence": report_json.get("evidence", []),
        "memory": {"markdown": _read_text(showcase_dir / "memory_trace.md")},
        "compression": {"markdown": _read_text(showcase_dir / "compression_trace.md")},
        "verification": {
            "markdown": _read_text(showcase_dir / "verifier_trace.md"),
            "claims": report_json.get("claims", []),
        },
        "repair": {
            "markdown": _read_text(showcase_dir / "redblue_trace.md"),
            "actions": report_json.get("repair_actions", []),
            "loop_trace": report_json.get("repair_loop_trace", []),
        },
        "eval": {"markdown": _read_text(showcase_dir / "eval_summary.md")},
        "llm_backend": {"markdown": _read_text(showcase_dir / "llm_backend.md")},
        "artifact_paths": _artifact_paths(showcase_dir),
    }


def _overview(report_json: dict[str, Any], run_summary: dict[str, Any]) -> dict[str, Any]:
    backend = run_summary.get("llm_backend") or "mock"
    writer_generation = run_summary.get("writer_generation", {})
    llm_usage = run_summary.get("llm_usage", {})
    question = report_json.get("question")
    question_summary = (
        re.split(r"\s+https?://", question, maxsplit=1)[0].strip()
        if isinstance(question, str)
        else question
    )
    if backend == "deepseek" and writer_generation.get("fallback") is False:
        boundary = (
            "Frozen real-source, real-embedding, real DeepSeek Writer run; "
            "one controlled run, not a production SLA."
        )
    else:
        boundary = (
            "Real-source demo runs may use mock generation and stay separate "
            "from frozen benchmark metrics."
        )
    return {
        "question": question_summary,
        "run_id": report_json.get("run_id") or run_summary.get("run_id"),
        "backend": backend,
        "model": run_summary.get("model"),
        "writer_mode": run_summary.get("writer_mode") or writer_generation.get("mode"),
        "writer_fallback": writer_generation.get("fallback"),
        "llm_total_tokens": llm_usage.get("total_tokens", 0),
        "llm_cost_usd": llm_usage.get(
            "cost_estimate_usd",
            run_summary.get("llm_total_cost_estimate", 0.0),
        ),
        "task_count": run_summary.get("task_count"),
        "evidence_count": run_summary.get("evidence_count"),
        "claim_count": len(report_json.get("claims", [])),
        "repair_count": run_summary.get("repair_count", len(report_json.get("repair_actions", []))),
        "corpus_path": run_summary.get("corpus_path"),
        "web_search_provider": run_summary.get("web_search_provider"),
        "live_source_count": run_summary.get("live_sources", {}).get("source_count", 0),
        "lineage_complete_rate": run_summary.get("live_sources", {}).get(
            "lineage_complete_rate", 0.0
        ),
        "cache_hit_rate": run_summary.get("live_sources", {}).get("cache_hit_rate", 0.0),
        "provider_event_count": run_summary.get("web_search_telemetry", {})
        .get("summary", {})
        .get("event_count", 0),
        "provider_operational_rate": run_summary.get("web_search_telemetry", {})
        .get("summary", {})
        .get("operational_rate", 0.0),
        "provider_retry_count": run_summary.get("web_search_telemetry", {})
        .get("summary", {})
        .get("total_retries", 0),
        "provider_circuit_open_count": run_summary.get("web_search_telemetry", {})
        .get("summary", {})
        .get("circuit_open_count", 0),
        "boundary": boundary,
    }


def _artifact_paths(showcase_dir: Path) -> dict[str, str]:
    names = (
        "index.md",
        "plan.md",
        "report.md",
        "report.json",
        "run_summary.json",
        "memory_trace.md",
        "compression_trace.md",
        "verifier_trace.md",
        "redblue_trace.md",
        "eval_summary.md",
        "llm_backend.md",
    )
    return {
        name: _display_path(showcase_dir / name)
        for name in names
        if (showcase_dir / name).exists()
    }


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _profile_payload(profile: Any) -> dict[str, Any]:
    payload = profile.to_dict()
    payload["built"] = profile.output_path.exists()
    payload["output_path"] = _display_path(profile.output_path)
    payload["source_dir"] = _display_path(profile.source_dir)
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_mermaid(markdown: str) -> str:
    marker = "```mermaid"
    if marker not in markdown:
        return ""
    start = markdown.find(marker) + len(marker)
    end = markdown.find("```", start)
    if end == -1:
        return markdown[start:].strip()
    return markdown[start:end].strip()


def _extract_plan_tasks(markdown: str) -> list[dict[str, str]]:
    tasks = []
    current: dict[str, str] | None = None
    for line in markdown.splitlines():
        if line.startswith("### task_"):
            if current:
                tasks.append(current)
            current = {"id": line.removeprefix("### ").strip()}
        elif current and line.startswith("- "):
            key, _, value = line[2:].partition(":")
            current[key.strip().replace(" ", "_")] = value.strip()
    if current:
        tasks.append(current)
    return tasks


def _deepseek_messages(question: str) -> list[LLMMessage]:
    return [
        LLMMessage(
            role="system",
            content=(
                "You are reviewing a DeepResearch Agent portfolio demo. Answer in Chinese, "
                "be concise, and do not invent benchmark numbers."
            ),
        ),
        LLMMessage(
            role="user",
            content=(
                f"问题：{question}\n\n"
                "请用 4 点说明这个项目为什么适合作为 AI Agent / AI 应用实习项目，"
                "再列出 2 个工程边界。"
            ),
        ),
    ]


app = create_app()
