from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepresearch_agent.agents.verifier import VerifierAgent
from deepresearch_agent.llm import LLMBackendConfig, LLMMessage, backend_status, create_llm_backend
from deepresearch_agent.schemas import Claim, Evidence
from deepresearch_agent.structured_output import StructuredOutputParser


ALLOWED_STATUSES = {
    "supported",
    "partial",
    "unsupported",
    "contradicted",
}


@dataclass(slots=True)
class VerifierSmokeConfig:
    cases_path: Path = Path("data/examples/llm_verifier_cases.jsonl")
    output_path: Path = Path("reports/llm_verifier_smoke.md")
    output_json_path: Path | None = None
    backend: str = "deepseek"
    model: str | None = "deepseek-v4-flash"
    run_real: bool = False
    limit: int | None = None
    max_tokens: int = 512


async def run_llm_verifier_smoke(config: VerifierSmokeConfig) -> dict[str, Any]:
    cases = _load_cases(config.cases_path)
    if config.limit is not None:
        cases = cases[: config.limit]

    heuristic = VerifierAgent()
    llm_config = LLMBackendConfig(
        backend=config.backend,
        model=config.model,
        max_tokens=config.max_tokens,
        max_retries=1,
    )
    status = backend_status(llm_config)
    should_call_llm = config.run_real and bool(status["env_configured"])
    backend = create_llm_backend(llm_config) if should_call_llm else None

    rows: list[dict[str, Any]] = []
    for case in cases:
        evidence = _case_evidence(case)
        claim = Claim(text=case["claim"], citation_ids=[evidence.id])
        checked = await heuristic.verify(claim, [evidence])
        llm_result = (
            await _run_llm_case(backend, case, evidence)
            if backend is not None
            else {
                "status": "skipped",
                "reason": "run_real=false or provider env is not configured",
                "parse_level": 0,
                "usage": {},
                "estimated_cost_rmb": 0.0,
            }
        )
        rows.append(
            {
                "id": case["id"],
                "claim": case["claim"],
                "expected_status": case["expected_status"],
                "heuristic_status": checked.verification_status.value,
                "heuristic_correct": checked.verification_status.value == case["expected_status"],
                "heuristic_reason": checked.verification_reason,
                "llm_status": llm_result["status"],
                "llm_correct": (
                    llm_result["status"] == case["expected_status"]
                    if llm_result["status"] != "skipped"
                    else None
                ),
                "llm_reason": llm_result["reason"],
                "parse_level": llm_result["parse_level"],
                "usage": llm_result["usage"],
                "estimated_cost_rmb": llm_result["estimated_cost_rmb"],
            }
        )

    summary = _summarize(rows, status, config)
    payload = {"summary": summary, "rows": rows}
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(to_markdown(payload), encoding="utf-8")
    if config.output_json_path is not None:
        config.output_json_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return payload


def _load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _case_evidence(case: dict[str, Any]) -> Evidence:
    return Evidence(
        task_id=case.get("task_id", "llm_verifier_smoke"),
        title=case.get("evidence_title", "Evidence"),
        text=case["evidence_text"],
        quote=case.get("quote"),
        url=case.get("url", f"case://{case['id']}"),
        source_id=case.get("source_id", "llm_verifier_smoke"),
        metadata={"trust_level": "high"},
        id=f"ev_{case['id']}",
        score=1.0,
    )


async def _run_llm_case(backend: Any, case: dict[str, Any], evidence: Evidence) -> dict[str, Any]:
    text = await backend.complete(_messages(case, evidence))
    parsed = StructuredOutputParser().parse(
        text,
        schema_defaults={
            "status": "unsupported",
            "reason": "parser fallback default",
        },
    )
    raw_status = str(parsed.data.get("status", "unsupported")).lower()
    status = raw_status if raw_status in ALLOWED_STATUSES else "unsupported"
    usage = getattr(backend, "last_usage", {}) or {}
    cost_usd = float(usage.get("cost_estimate_usd", 0.0) or 0.0)
    return {
        "status": status,
        "reason": str(parsed.data.get("reason", ""))[:600],
        "parse_level": parsed.parse_level,
        "usage": usage,
        "estimated_cost_rmb": round(cost_usd * 7.25, 8),
    }


def _messages(case: dict[str, Any], evidence: Evidence) -> list[LLMMessage]:
    return [
        LLMMessage(
            role="system",
            content=(
                "You are a strict claim verification judge. Return only JSON. "
                "Allowed status values: supported, partial, unsupported, contradicted."
            ),
        ),
        LLMMessage(
            role="user",
            content=(
                f"Claim:\n{case['claim']}\n\n"
                f"Evidence title:\n{evidence.title}\n\n"
                f"Evidence text:\n{evidence.text}\n\n"
                f"Quoted span:\n{evidence.quote or ''}\n\n"
                "Decide whether the evidence supports the claim. "
                "Return JSON exactly like: {\"status\":\"supported\",\"reason\":\"...\"}"
            ),
        ),
    ]


def _summarize(
    rows: list[dict[str, Any]],
    status: dict[str, Any],
    config: VerifierSmokeConfig,
) -> dict[str, Any]:
    attempted = [row for row in rows if row["llm_status"] != "skipped"]
    llm_correct = [row for row in attempted if row["llm_correct"]]
    heuristic_correct = [row for row in rows if row["heuristic_correct"]]
    total_cost = sum(float(row["estimated_cost_rmb"] or 0.0) for row in rows)
    total_tokens = sum(int(row["usage"].get("total_tokens", 0) or 0) for row in rows)
    expected_counts = Counter(str(row["expected_status"]) for row in rows)
    heuristic_counts = Counter(str(row["heuristic_status"]) for row in rows)
    llm_counts = Counter(str(row["llm_status"]) for row in rows)
    confusion = _confusion_matrix(rows)
    per_status = _per_expected_status(rows)
    error_cases = [
        {
            "id": row["id"],
            "expected_status": row["expected_status"],
            "heuristic_status": row["heuristic_status"],
            "llm_status": row["llm_status"],
            "claim": row["claim"],
            "llm_reason": row["llm_reason"],
        }
        for row in rows
        if row["llm_status"] != "skipped" and row["llm_status"] != row["expected_status"]
    ]
    return {
        "case_count": len(rows),
        "backend": status["backend"],
        "model": status["model"],
        "run_real": config.run_real,
        "env_configured": status["env_configured"],
        "heuristic_accuracy": len(heuristic_correct) / len(rows) if rows else 0.0,
        "llm_attempted": len(attempted),
        "llm_accuracy": len(llm_correct) / len(attempted) if attempted else None,
        "llm_error_count": len(attempted) - len(llm_correct),
        "expected_status_counts": dict(sorted(expected_counts.items())),
        "heuristic_status_counts": dict(sorted(heuristic_counts.items())),
        "llm_status_counts": dict(sorted(llm_counts.items())),
        "confusion_matrix": confusion,
        "per_expected_status": per_status,
        "error_cases": error_cases[:30],
        "total_tokens": total_tokens,
        "estimated_cost_rmb": round(total_cost, 8),
        "boundary": "LLM verifier smoke is a provider/second-layer check and is not part of offline benchmark metrics.",
    }


def _confusion_matrix(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    statuses = ["supported", "partial", "unsupported", "contradicted", "skipped"]
    matrix = {
        expected: {actual: 0 for actual in statuses}
        for expected in ["supported", "partial", "unsupported", "contradicted"]
    }
    for row in rows:
        expected = str(row["expected_status"])
        actual = str(row["llm_status"])
        if expected not in matrix:
            continue
        if actual not in matrix[expected]:
            matrix[expected][actual] = 0
        matrix[expected][actual] += 1
    return matrix


def _per_expected_status(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for status_name in ["supported", "partial", "unsupported", "contradicted"]:
        bucket = [row for row in rows if row["expected_status"] == status_name]
        attempted = [row for row in bucket if row["llm_status"] != "skipped"]
        correct = [row for row in attempted if row["llm_status"] == row["expected_status"]]
        summary[status_name] = {
            "n": len(bucket),
            "attempted": len(attempted),
            "correct": len(correct),
            "accuracy": len(correct) / len(attempted) if attempted else 0.0,
        }
    return summary


def to_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# LLM Verifier Smoke",
        "",
        "This smoke test compares the existing heuristic verifier with an optional LLM second-layer judge on a balanced claim/evidence set.",
        "",
        "## Summary",
        "",
        f"- cases: `{summary['case_count']}`",
        f"- backend: `{summary['backend']}`",
        f"- model: `{summary['model']}`",
        f"- run_real: `{str(summary['run_real']).lower()}`",
        f"- env_configured: `{str(summary['env_configured']).lower()}`",
        f"- heuristic_accuracy: `{summary['heuristic_accuracy']:.3f}`",
        f"- llm_attempted: `{summary['llm_attempted']}`",
        f"- llm_accuracy: `{summary['llm_accuracy'] if summary['llm_accuracy'] is not None else 'n/a'}`",
        f"- llm_error_count: `{summary['llm_error_count']}`",
        f"- total_tokens: `{summary['total_tokens']}`",
        f"- estimated_cost_rmb: `{summary['estimated_cost_rmb']}`",
        f"- boundary: {summary['boundary']}",
        "",
        "## Status Distribution",
        "",
        f"- expected: `{summary['expected_status_counts']}`",
        f"- heuristic: `{summary['heuristic_status_counts']}`",
        f"- llm: `{summary['llm_status_counts']}`",
        "",
        "## Per Expected Status",
        "",
        "| expected | n | attempted | correct | accuracy |",
        "| --- | ---:| ---:| ---:| ---:|",
    ]
    for status_name, item in summary["per_expected_status"].items():
        lines.append(
            f"| {status_name} | {item['n']} | {item['attempted']} | {item['correct']} | {item['accuracy']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Confusion Matrix",
            "",
            "| expected \\ llm | supported | partial | unsupported | contradicted | skipped |",
            "| --- | ---:| ---:| ---:| ---:| ---:|",
        ]
    )
    for expected, counts in summary["confusion_matrix"].items():
        lines.append(
            "| {expected} | {supported} | {partial} | {unsupported} | {contradicted} | {skipped} |".format(
                expected=expected,
                supported=counts.get("supported", 0),
                partial=counts.get("partial", 0),
                unsupported=counts.get("unsupported", 0),
                contradicted=counts.get("contradicted", 0),
                skipped=counts.get("skipped", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Error Cases",
            "",
        ]
    )
    errors = summary.get("error_cases", [])
    if not errors:
        lines.append("- No LLM errors recorded.")
    for error in errors[:20]:
        lines.append(
            "- `{id}` expected={expected_status} heuristic={heuristic_status} llm={llm_status}: {claim}".format(
                **error
            )
        )
    lines.extend(
        [
            "",
        "## Cases",
        "",
        "| id | expected | heuristic | llm | cost_rmb |",
        "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| {id} | {expected_status} | {heuristic_status} | {llm_status} | {estimated_cost_rmb} |".format(
                **row
            )
        )
    return "\n".join(lines)
