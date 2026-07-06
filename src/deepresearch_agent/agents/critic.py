from __future__ import annotations

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.schemas import AttackCategory, AttackFinding, ResearchReport, VerificationStatus


class CriticAgent(BaseAgent):
    name = "critic"

    async def _run(self, agent_input: object, context=None) -> list[AttackFinding]:
        if not isinstance(agent_input, ResearchReport):
            raise TypeError("CriticAgent.run expects a ResearchReport.")
        return await self.review(agent_input)

    async def review(self, report: ResearchReport) -> list[AttackFinding]:
        findings: list[AttackFinding] = []
        modified_claims = {
            action.target_claim_id
            for action in report.repair_actions
            if action.action_type.value == "modify"
        }
        for claim in report.claims:
            if not claim.citation_ids:
                findings.append(
                    AttackFinding(
                        target_claim_id=claim.id,
                        category=AttackCategory.CITATION,
                        severity=4,
                        reason="Claim has no citation ids.",
                        suggested_check="Attach evidence or delete the claim.",
                    )
                )
            if claim.verification_status in {
                VerificationStatus.UNSUPPORTED,
                VerificationStatus.CONTRADICTED,
            }:
                findings.append(
                    AttackFinding(
                        target_claim_id=claim.id,
                        category=AttackCategory.FACTUALITY,
                        severity=4,
                        reason=f"Claim verification status is {claim.verification_status.value}.",
                        suggested_check="Modify or delete unsupported content.",
                    )
                )
            elif claim.verification_status == VerificationStatus.PARTIAL and claim.id not in modified_claims:
                severity = 1 if self._looks_vague(claim.text) else 2
                findings.append(
                    AttackFinding(
                        target_claim_id=claim.id,
                        category=AttackCategory.FACTUALITY,
                        severity=severity,
                        reason="Claim is only partially supported by cited evidence.",
                        suggested_check="Qualify wording or add stronger evidence.",
                    )
                )
        cited_ids = {cid for claim in report.claims for cid in claim.citation_ids}
        if report.evidence and len(cited_ids) < max(1, min(3, len(report.evidence))):
            findings.append(
                AttackFinding(
                    target_claim_id=None,
                    category=AttackCategory.OMISSION,
                    severity=2,
                    reason="Some high-ranked evidence is not reflected in the claims.",
                    suggested_check="Add a cautious claim or limitation from unused evidence.",
                )
            )
        return findings

    def _looks_vague(self, text: str) -> bool:
        lowered = text.lower()
        vague_terms = {"might", "could", "somehow", "various", "things", "可能", "一些", "相关"}
        return any(term in lowered for term in vague_terms)
