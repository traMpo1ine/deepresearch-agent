from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import uuid4

from deepresearch_agent.schemas.serialization import to_jsonable


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def utc_now() -> datetime:
    return datetime.now(UTC)


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    BLOCKED = "blocked"
    REPAIRING = "repairing"
    VERIFIED = "verified"


class TaskType(str, Enum):
    ROOT = "root"
    SEARCH = "search"
    READ = "read"
    SYNTHESIZE = "synthesize"
    VERIFY = "verify"
    REPAIR = "repair"


class PlanType(str, Enum):
    GENERAL = "general"
    COMPARISON = "comparison"
    RISK_ANALYSIS = "risk_analysis"
    SOLUTION_DESIGN = "solution_design"


class VerificationStatus(str, Enum):
    UNKNOWN = "unknown"
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


class RepairActionType(str, Enum):
    ADD = "add"
    DELETE = "delete"
    MODIFY = "modify"
    VERIFY = "verify"


class AttackCategory(str, Enum):
    FACTUALITY = "factuality"
    LOGIC = "logic"
    CITATION = "citation"
    OMISSION = "omission"


T = TypeVar("T")


@dataclass(slots=True)
class AgentResult(Generic[T]):
    """Standard wrapper for agent outputs, errors, latency, and debug metadata."""

    agent_name: str
    ok: bool
    output: T | None = None
    error: str | None = None
    latency_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AtomicVerificationResult:
    """Verifier decision for one small, independently checkable claim."""

    text: str
    status: VerificationStatus
    support_terms: list[str]
    missing_terms: list[str]
    term_overlap: float
    quote_overlap: float
    contradiction_cues: list[str] = field(default_factory=list)
    evidence_id: str | None = None
    best_quote: str | None = None
    decision_reason: str = ""
    evidence_scores: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""


@dataclass(slots=True)
class PlanQualityReport:
    task_count: int
    dependency_count: int
    has_background: bool
    has_implementation: bool
    has_risk: bool
    has_evaluation: bool
    has_tradeoffs: bool
    issues: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.issues


@dataclass(slots=True)
class ResearchTask:
    """A DAG node representing one planned research action."""

    question: str
    id: str = field(default_factory=lambda: new_id("task"))
    task_type: TaskType = TaskType.SEARCH
    parent_id: str | None = None
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    expected_evidence: str = ""
    retry_count: int = 0
    max_retries: int = 1
    timeout_seconds: float = 30.0
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

@dataclass(slots=True)
class ResearchPlan:
    """Planner output that can be persisted and directly compiled into a DAG."""

    root_question: str
    tasks: list[ResearchTask]
    rationale: str
    plan_type: PlanType = PlanType.GENERAL
    sub_questions: list[str] = field(default_factory=list)
    quality_report: PlanQualityReport | None = None

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable(self)


@dataclass(slots=True)
class Evidence:
    """Inspectable source snippet used to ground claims and citations."""

    task_id: str
    title: str
    text: str
    url: str = "mock://local"
    quote: str | None = None
    source_id: str = "local"
    chunk_id: str | None = None
    quote_start: int | None = None
    quote_end: int | None = None
    score: float = 0.0
    id: str = field(default_factory=lambda: new_id("ev"))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VerificationTrace:
    """Audit trail explaining how one claim was matched against evidence."""

    claim_id: str
    status: VerificationStatus
    matched_evidence_ids: list[str]
    support_terms: list[str]
    missing_terms: list[str]
    reason: str
    citation_presence: bool = False
    term_overlap: float = 0.0
    quote_overlap: float = 0.0
    contradiction_cues: list[str] = field(default_factory=list)
    support_level: str = "unknown"
    atomic_claims: list[str] = field(default_factory=list)
    atomic_results: list[AtomicVerificationResult] = field(default_factory=list)
    id: str = field(default_factory=lambda: new_id("trace"))


@dataclass(slots=True)
class Claim:
    """Report assertion that should be grounded by citation ids."""

    text: str
    citation_ids: list[str]
    id: str = field(default_factory=lambda: new_id("claim"))
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    confidence: float = 0.0
    needs_verification: bool = False
    verification_reason: str = ""
    matched_evidence_ids: list[str] = field(default_factory=list)
    missing_terms: list[str] = field(default_factory=list)
    verification_trace: VerificationTrace | None = None


@dataclass(slots=True)
class ReportSection:
    title: str
    body: str
    claim_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CompressedSentence:
    text: str
    evidence_id: str
    source_id: str
    score: float
    preserved_quote: bool = False


@dataclass(slots=True)
class CompressedContext:
    question: str
    sentences: list[CompressedSentence]
    original_char_count: int
    compressed_char_count: int

    @property
    def compression_ratio(self) -> float:
        if self.original_char_count == 0:
            return 1.0
        return self.compressed_char_count / self.original_char_count

    def to_text(self) -> str:
        return "\n".join(
            f"[{sentence.evidence_id}] {sentence.text}" for sentence in self.sentences
        )


@dataclass(slots=True)
class RepairAction:
    """Auditable Red-Blue patch with before/after text when available."""

    action_type: RepairActionType
    target_claim_id: str
    reason: str
    patch: str
    before: str | None = None
    after: str | None = None
    id: str = field(default_factory=lambda: new_id("repair"))


@dataclass(slots=True)
class RepairLoopTrace:
    """One verify-repair loop iteration with convergence and oscillation signals."""

    round_index: int
    finding_count: int
    weak_claim_count: int
    repair_action_count: int
    claim_fingerprint_before: str
    claim_fingerprint_after: str
    converged: bool = False
    oscillating: bool = False
    stop_reason: str = ""
    id: str = field(default_factory=lambda: new_id("repair_loop"))


@dataclass(slots=True)
class AttackFinding:
    """Red Agent finding describing a claim-level or report-level weakness."""

    target_claim_id: str | None
    category: AttackCategory
    severity: int
    reason: str
    suggested_check: str
    id: str = field(default_factory=lambda: new_id("attack"))


@dataclass(slots=True)
class ResearchReport:
    """Structured research output with claims, citations, traces, and repairs."""

    question: str
    title: str
    summary: str
    claims: list[Claim]
    evidence: list[Evidence]
    sections: list[ReportSection] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    repair_actions: list[RepairAction] = field(default_factory=list)
    repair_loop_trace: list[RepairLoopTrace] = field(default_factory=list)
    run_id: str | None = None
    run_summary: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"**Question:** {self.question}",
            "",
            "## Summary",
            "",
            self.summary,
            "",
        ]
        if self.sections:
            lines.extend(["## Sections", ""])
            for section in self.sections:
                lines.extend([f"### {section.title}", "", section.body, ""])
        lines.extend([
            "## Key Claims",
            "",
        ])
        for index, claim in enumerate(self.claims, start=1):
            citations = ", ".join(f"[{cid}]" for cid in claim.citation_ids) or "[no citation]"
            lines.append(
                f"{index}. {claim.text} {citations} "
                f"({claim.verification_status.value}, confidence={claim.confidence:.2f})"
            )
            if claim.verification_reason:
                lines.append(f"   - verification: {claim.verification_reason}")
        lines.extend(["", "## Evidence", ""])
        for item in self.evidence:
            quote = f" Quote: {item.quote}" if item.quote else ""
            chunk = f", chunk={item.chunk_id}" if item.chunk_id else ""
            locator_value = item.metadata.get("citation_locator")
            locator = f", locator={locator_value}" if locator_value else ""
            lines.append(f"- [{item.id}] {item.title} ({item.url}{chunk}{locator}).{quote}")
        if self.limitations:
            lines.extend(["", "## Limitations", ""])
            for limitation in self.limitations:
                lines.append(f"- {limitation}")
        if self.repair_actions:
            lines.extend(["", "## Repair Actions", ""])
            for action in self.repair_actions:
                lines.append(
                    f"- {action.action_type.value.upper()} {action.target_claim_id}: {action.reason}"
                )
        return "\n".join(lines)


@dataclass(slots=True)
class JudgeScore:
    factuality: float
    coverage: float
    citation_quality: float
    structure: float
    usefulness: float

    @property
    def overall(self) -> float:
        return (
            self.factuality
            + self.coverage
            + self.citation_quality
            + self.structure
            + self.usefulness
        ) / 5


@dataclass(slots=True)
class EvaluationResult:
    question_id: str
    factual_accuracy: float
    hallucination_rate: float
    citation_coverage: float
    unsupported_claim_rate: float
    judge_score: JudgeScore
    answer_type: str = "general"
    weak_support_rate: float = 0.0
    evidence_reuse_rate: float = 0.0
    compression_ratio: float = 1.0
    repair_success_rate: float = 0.0
    atomic_support_rate: float = 0.0
    contradiction_detection_rate: float = 0.0
    repair_precision: float = 0.0
    repair_coverage: float = 0.0
    repair_convergence_rate: float = 0.0
    repair_oscillation_rate: float = 0.0
    avg_repair_rounds: float = 0.0
    evidence_grounding_score: float = 0.0
    avg_task_latency: float = 0.0
    domain: str = "general"
    required_hops: int = 1
    hotpot_style: bool = False
    repair_action_counts: dict[str, int] = field(default_factory=dict)
    failure_analysis: list[str] = field(default_factory=list)
    bootstrap_ci: tuple[float, float] | None = None
    cohens_d: float | None = None
