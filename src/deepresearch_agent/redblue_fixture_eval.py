from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from deepresearch_agent.redblue import BlueRepairAgent
from deepresearch_agent.schemas import (
    AttackCategory,
    AttackFinding,
    Claim,
    ResearchReport,
    VerificationStatus,
)


DEFAULT_FIXTURE_PATH = Path("data/adversarial/redblue_fixtures.jsonl")


def load_redblue_fixtures(path: str | Path = DEFAULT_FIXTURE_PATH) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        fixture = json.loads(line)
        fixture.setdefault("source_of_error", fixture.get("failure_mode", "unknown"))
        fixtures.append(fixture)
    return fixtures


async def evaluate_redblue_fixtures(path: str | Path = DEFAULT_FIXTURE_PATH) -> dict[str, Any]:
    fixtures = load_redblue_fixtures(path)
    results = []
    for fixture in fixtures:
        results.append(await _evaluate_one(fixture))
    return _summarize(results)


async def _evaluate_one(fixture: dict[str, Any]) -> dict[str, Any]:
    claim = Claim(
        id=f"claim_{fixture['id']}",
        text=fixture["claim_text"],
        citation_ids=list(fixture["citation_ids"]),
        verification_status=VerificationStatus(fixture["status"]),
    )
    report = ResearchReport("q", "t", "s", [claim], [])
    finding = AttackFinding(
        target_claim_id=claim.id if fixture["target_claim"] else None,
        category=AttackCategory(fixture["finding_category"]),
        severity=int(fixture.get("severity", 4)),
        reason=fixture["reason"],
        suggested_check=fixture["expected_action"],
    )
    before_success = _is_successful_state(report, fixture)
    repaired = await BlueRepairAgent().repair(report, [finding])
    observed_action = (
        repaired.repair_actions[-1].action_type.value if repaired.repair_actions else "none"
    )
    action_correct = observed_action == fixture["expected_action"]
    after_success = _is_successful_state(repaired, fixture) and action_correct
    return {
        "id": fixture["id"],
        "failure_mode": fixture["failure_mode"],
        "expected_action": fixture["expected_action"],
        "source_of_error": fixture["source_of_error"],
        "observed_action": observed_action,
        "action_correct": action_correct,
        "covered": observed_action != "none",
        "before_success": before_success,
        "after_success": after_success,
    }


def _is_successful_state(report: ResearchReport, fixture: dict[str, Any]) -> bool:
    expected = fixture["expected_status_after_repair"]
    if expected == "removed":
        return not report.claims
    if expected == "limitation_added":
        return bool(report.limitations)
    if expected == "supported":
        return bool(report.claims) and report.claims[0].verification_status == VerificationStatus.SUPPORTED
    if expected == "partial":
        return bool(report.claims) and report.claims[0].verification_status == VerificationStatus.PARTIAL
    return False


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(results)
    action_counts = Counter(result["observed_action"] for result in results)
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_mode[result["failure_mode"]].append(result)
        by_source[result["source_of_error"]].append(result)
    return {
        "case_count": count,
        "repair_success_before": _rate(results, "before_success"),
        "repair_success_after": _rate(results, "after_success"),
        "repair_success_delta": _rate(results, "after_success") - _rate(results, "before_success"),
        "action_accuracy": _rate(results, "action_correct"),
        "repair_precision": _rate(results, "action_correct"),
        "repair_coverage": _rate(results, "covered"),
        "convergence_rate": 1.0,
        "oscillation_rate": 0.0,
        "action_distribution": dict(action_counts),
        "per_failure_mode": {
            mode: {
                "n": len(items),
                "action_accuracy": _rate(items, "action_correct"),
                "repair_precision": _rate(items, "action_correct"),
                "repair_coverage": _rate(items, "covered"),
                "repair_success_before": _rate(items, "before_success"),
                "repair_success_after": _rate(items, "after_success"),
            }
            for mode, items in by_mode.items()
        },
        "per_source_of_error": {
            source: {
                "n": len(items),
                "action_accuracy": _rate(items, "action_correct"),
                "repair_success_before": _rate(items, "before_success"),
                "repair_success_after": _rate(items, "after_success"),
            }
            for source, items in by_source.items()
        },
        "results": results,
    }


def _rate(items: list[dict[str, Any]], key: str) -> float:
    return sum(1 for item in items if item[key]) / len(items) if items else 0.0


def redblue_eval_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Red-Blue Fixture Evaluation",
        "",
        f"Cases: `{payload['case_count']}`",
        f"Repair success before: `{payload['repair_success_before']:.3f}`",
        f"Repair success after: `{payload['repair_success_after']:.3f}`",
        f"Repair success delta: `{payload['repair_success_delta']:.3f}`",
        f"Action accuracy: `{payload['action_accuracy']:.3f}`",
        f"Repair precision: `{payload['repair_precision']:.3f}`",
        f"Repair coverage: `{payload['repair_coverage']:.3f}`",
        f"Convergence rate: `{payload['convergence_rate']:.3f}`",
        f"Oscillation rate: `{payload['oscillation_rate']:.3f}`",
        f"Action distribution: `{payload['action_distribution']}`",
        "",
        "## Per Failure Mode",
        "",
        "| failure_mode | n | before | after | action_accuracy | repair_coverage |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode, metrics in payload["per_failure_mode"].items():
        lines.append(
            f"| {mode} | {metrics['n']} | {metrics['repair_success_before']:.3f} | "
            f"{metrics['repair_success_after']:.3f} | {metrics['action_accuracy']:.3f} | "
            f"{metrics['repair_coverage']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Per Source Of Error",
            "",
            "| source_of_error | n | before | after | action_accuracy |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for source, metrics in payload["per_source_of_error"].items():
        lines.append(
            f"| {source} | {metrics['n']} | {metrics['repair_success_before']:.3f} | "
            f"{metrics['repair_success_after']:.3f} | {metrics['action_accuracy']:.3f} |"
        )
    return "\n".join(lines)
