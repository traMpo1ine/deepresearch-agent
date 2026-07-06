from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from deepresearch_agent.corpus_profiles import (
    ensure_profile_built,
    list_corpus_profiles,
)
from deepresearch_agent.llm import LLMBackendConfig, LLMMessage, backend_status, create_llm_backend
from deepresearch_agent.showcase import build_showcase

try:
    from fastapi import BackgroundTasks, FastAPI, HTTPException
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
    ROOT / "reports" / "final" / "final_sprint_check" / "showcase",
    ROOT / "reports" / "showcase" / "final_check",
)
DEMO_RUNS_DIR = ROOT / "reports" / "demo_runs"


class RunRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    backend: str = "mock"
    model: str | None = None
    repair_rounds: int = Field(default=2, ge=0, le=5)
    corpus_profile: str = "offline_agent_docs"


class DeepSeekShowcaseRequest(BaseModel):
    run_real: bool = False
    question: str = "为什么 DeepResearch Agent 需要引用验证和 Red-Blue 修复？"
    model: str = "deepseek-v4-flash"
    max_tokens: int = Field(default=512, ge=64, le=2048)


@dataclass(slots=True)
class DemoRun:
    run_id: str
    question: str
    backend: str
    model: str | None
    repair_rounds: int
    corpus_profile: str
    corpus_path: Path
    output_dir: Path
    status: str = "queued"
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "question": self.question,
            "backend": self.backend,
            "model": self.model,
            "repair_rounds": self.repair_rounds,
            "corpus_profile": self.corpus_profile,
            "corpus_path": _display_path(self.corpus_path),
            "output_dir": _display_path(self.output_dir),
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "artifact_paths": _artifact_paths(self.output_dir),
        }

    def mark(self, status: str, error: str | None = None) -> None:
        self.status = status
        self.error = error
        self.updated_at = datetime.now(UTC).isoformat()


RUNS: dict[str, DemoRun] = {}


def create_app() -> FastAPI:
    app = FastAPI(
        title="DeepResearch Agent Demo",
        description="Local FastAPI demo for the offline DeepResearch Agent showcase.",
        version="0.1.0",
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        status = backend_status(LLMBackendConfig(backend="deepseek"))
        return {
            "ok": True,
            "app": "deepresearch-agent-demo",
            "version": "0.1.0",
            "default_backend": "mock",
            "deepseek_env_configured": status["env_configured"],
            "deepseek_model": status["model"],
            "corpus_profiles": [_profile_payload(profile) for profile in list_corpus_profiles()],
            "boundary": "New demo runs use mock/offline by default; real providers are smoke-only.",
        }

    @app.get("/api/corpus-profiles")
    async def corpus_profiles() -> dict[str, Any]:
        return {"profiles": [_profile_payload(profile) for profile in list_corpus_profiles()]}

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

    @app.post("/api/runs")
    async def start_run(request: RunRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
        if request.backend != "mock":
            raise HTTPException(
                status_code=400,
                detail="Demo runs only allow backend='mock'. Use /api/deepseek-showcase for provider smoke.",
            )
        try:
            corpus_path = ensure_profile_built(request.corpus_profile)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        run_id = f"demo_{uuid4().hex[:12]}"
        output_dir = DEMO_RUNS_DIR / run_id
        job = DemoRun(
            run_id=run_id,
            question=request.question,
            backend=request.backend,
            model=request.model,
            repair_rounds=request.repair_rounds,
            corpus_profile=request.corpus_profile,
            corpus_path=corpus_path,
            output_dir=output_dir,
        )
        RUNS[run_id] = job
        background_tasks.add_task(_run_showcase_job, job)
        return job.to_dict()

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str) -> dict[str, Any]:
        return _get_job(run_id).to_dict()

    @app.get("/api/runs/{run_id}/artifacts")
    async def get_run_artifacts(run_id: str) -> dict[str, Any]:
        job = _get_job(run_id)
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


async def _run_showcase_job(job: DemoRun) -> None:
    job.mark("running")
    try:
        await build_showcase(
            question=job.question,
            output_dir=job.output_dir,
            llm_backend="mock",
            model=job.model,
            repair_rounds=job.repair_rounds,
            corpus_path=job.corpus_path,
        )
        job.mark("succeeded")
    except Exception as exc:  # noqa: BLE001 - background job state should preserve failures.
        job.mark("failed", str(exc))


def _get_job(run_id: str) -> DemoRun:
    job = RUNS.get(run_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown demo run: {run_id}")
    return job


def _find_default_showcase() -> Path | None:
    for candidate in DEFAULT_SHOWCASE_CANDIDATES:
        if (candidate / "index.md").exists():
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
    return {
        "question": report_json.get("question"),
        "run_id": report_json.get("run_id") or run_summary.get("run_id"),
        "backend": run_summary.get("llm_backend"),
        "model": run_summary.get("model"),
        "task_count": run_summary.get("task_count"),
        "evidence_count": run_summary.get("evidence_count"),
        "claim_count": len(report_json.get("claims", [])),
        "repair_count": run_summary.get("repair_count", len(report_json.get("repair_actions", []))),
        "corpus_path": run_summary.get("corpus_path"),
        "boundary": "Offline/mock benchmark metrics stay separate from real provider smoke outputs.",
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
