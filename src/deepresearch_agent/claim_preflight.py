from __future__ import annotations

from dataclasses import dataclass, field

from deepresearch_agent.schemas import Claim, Evidence, VerificationStatus


CONFLICT_CUES = {
    "however",
    "but",
    "contradict",
    "conflict",
    "not always",
    "cannot",
    "不能",
    "并非",
    "相反",
}
OVERCLAIM_CUES = {"always", "never", "guarantees", "perfect", "完全", "所有", "绝对"}


@dataclass(slots=True)
class ClaimPreflightReport:
    duplicate_claim_ids: list[str] = field(default_factory=list)
    conflict_evidence_ids: list[str] = field(default_factory=list)
    downgraded_claim_ids: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class ClaimPreflight:
    """Lightweight write-time guard before full verifier and Red-Blue repair."""

    def run(self, claims: list[Claim], evidence: list[Evidence]) -> ClaimPreflightReport:
        report = ClaimPreflightReport()
        self._dedupe_claims(claims, report)
        self._detect_conflicts(evidence, report)
        self._downgrade_overclaims(claims, report)
        if report.duplicate_claim_ids:
            report.limitations.append("Duplicate claims were removed before report verification.")
        if report.conflict_evidence_ids:
            report.limitations.append(
                "Some retrieved evidence contains conflict cues; related claims should be stated cautiously."
            )
        if report.downgraded_claim_ids:
            report.limitations.append("Over-strong claims were downgraded before verification.")
        return report

    def _dedupe_claims(self, claims: list[Claim], report: ClaimPreflightReport) -> None:
        seen: set[str] = set()
        kept: list[Claim] = []
        for claim in claims:
            key = " ".join(claim.text.lower().split())
            if key in seen:
                report.duplicate_claim_ids.append(claim.id)
                continue
            seen.add(key)
            kept.append(claim)
        claims[:] = kept

    def _detect_conflicts(self, evidence: list[Evidence], report: ClaimPreflightReport) -> None:
        for item in evidence:
            text = f"{item.title} {item.text} {item.quote or ''}".lower()
            if any(cue in text for cue in CONFLICT_CUES):
                report.conflict_evidence_ids.append(item.id)

    def _downgrade_overclaims(self, claims: list[Claim], report: ClaimPreflightReport) -> None:
        for claim in claims:
            text = claim.text.lower()
            if any(cue in text for cue in OVERCLAIM_CUES):
                if not claim.text.startswith("Evidence suggests that "):
                    claim.text = f"Evidence suggests that {claim.text}"
                claim.confidence = min(claim.confidence, 0.60)
                claim.verification_status = VerificationStatus.PARTIAL
                claim.needs_verification = True
                report.downgraded_claim_ids.append(claim.id)
