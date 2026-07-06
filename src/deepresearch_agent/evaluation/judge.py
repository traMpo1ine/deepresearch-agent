from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from deepresearch_agent.schemas import JudgeScore, ResearchReport, VerificationStatus


@dataclass(slots=True)
class BenchmarkCase:
    id: str
    question: str
    gold_points: list[str]
    tags: list[str]
    required_sources: list[str]
    must_not_claim: list[str]
    difficulty: str
    answer_type: str = "general"
    required_hops: int = 1
    domain: str = "general"
    hotpot_style: bool = False
    expected_failure_modes: list[str] | None = None
    must_cite_sources: list[str] | None = None


class JudgeBackend(Protocol):
    async def score(self, report: ResearchReport, case: BenchmarkCase) -> JudgeScore:
        """Score a report against a benchmark case."""


class MockJudgeBackend:
    async def score(self, report: ResearchReport, case: BenchmarkCase) -> JudgeScore:
        report_text = report.to_markdown().lower()
        gold_hits = sum(1 for point in case.gold_points if self._overlap(point, report_text) > 0)
        coverage = gold_hits / max(len(case.gold_points), 1)
        unsupported = sum(
            1
            for claim in report.claims
            if claim.needs_verification
            or claim.verification_status
            in {VerificationStatus.UNKNOWN, VerificationStatus.UNSUPPORTED, VerificationStatus.CONTRADICTED}
        )
        factuality = 1.0 - unsupported / max(len(report.claims), 1)
        citation_quality = sum(1 for claim in report.claims if claim.citation_ids) / max(len(report.claims), 1)
        structure = 1.0 if report.sections and report.limitations else 0.7
        usefulness = min(1.0, 0.4 + coverage * 0.4 + citation_quality * 0.2)
        return JudgeScore(
            factuality=factuality,
            coverage=coverage,
            citation_quality=citation_quality,
            structure=structure,
            usefulness=usefulness,
        )

    def _overlap(self, point: str, report_text: str) -> int:
        terms = [term.lower() for term in point.replace("/", " ").split() if len(term) > 3]
        return sum(1 for term in terms if term in report_text)
