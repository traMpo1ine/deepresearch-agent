from __future__ import annotations

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.schemas import (
    AttackCategory,
    AttackFinding,
    RepairAction,
    RepairActionType,
    ResearchReport,
    VerificationStatus,
)


class BlueRepairAgent(BaseAgent):
    name = "blue_repair"

    async def _run(self, agent_input: object, context=None) -> ResearchReport:
        if not isinstance(agent_input, dict):
            raise TypeError("BlueRepairAgent.run expects {'report': ResearchReport, 'findings': list[AttackFinding]}.")
        report = agent_input.get("report")
        findings = agent_input.get("findings")
        if not isinstance(report, ResearchReport) or not isinstance(findings, list):
            raise TypeError("BlueRepairAgent.run expects {'report': ResearchReport, 'findings': list[AttackFinding]}.")
        return await self.repair(report, findings)

    async def repair(self, report: ResearchReport, findings: list[AttackFinding]) -> ResearchReport:
        for finding in findings:
            if finding.target_claim_id is None:
                self._add_limitation(report, finding)
                continue
            claim_id = finding.target_claim_id
            for claim in report.claims:
                if claim.id != claim_id:
                    continue
                if finding.category == AttackCategory.CITATION and not claim.citation_ids and finding.severity >= 4:
                    self._delete_claim(report, claim.id, finding)
                elif claim.verification_status in {
                    VerificationStatus.UNSUPPORTED,
                    VerificationStatus.CONTRADICTED,
                } and finding.severity >= 4:
                    self._delete_claim(report, claim.id, finding)
                elif claim.verification_status in {
                    VerificationStatus.PARTIAL,
                    VerificationStatus.UNSUPPORTED,
                    VerificationStatus.CONTRADICTED,
                }:
                    self._modify_claim(report, claim.id, finding)
                else:
                    report.repair_actions.append(
                        RepairAction(
                            action_type=RepairActionType.VERIFY,
                            target_claim_id=claim.id,
                            reason=finding.reason,
                            patch="No text change; claim already passed current verifier.",
                            before=claim.text,
                            after=claim.text,
                        )
                    )
        return report

    def _modify_claim(self, report: ResearchReport, claim_id: str, finding: AttackFinding) -> None:
        for claim in report.claims:
            if claim.id != claim_id:
                continue
            before = claim.text
            if not claim.text.startswith("Evidence suggests that "):
                claim.text = f"Evidence suggests that {claim.text}"
            claim.verification_status = VerificationStatus.PARTIAL
            claim.confidence = min(claim.confidence, 0.60)
            report.repair_actions.append(
                RepairAction(
                    action_type=RepairActionType.MODIFY,
                    target_claim_id=claim.id,
                    reason=finding.reason,
                    patch="Qualified wording for partially supported claim.",
                    before=before,
                    after=claim.text,
                )
            )

    def _delete_claim(self, report: ResearchReport, claim_id: str, finding: AttackFinding) -> None:
        for index, claim in enumerate(report.claims):
            if claim.id != claim_id:
                continue
            before = claim.text
            del report.claims[index]
            report.repair_actions.append(
                RepairAction(
                    action_type=RepairActionType.DELETE,
                    target_claim_id=claim_id,
                    reason=finding.reason,
                    patch="Removed unsupported or uncited claim.",
                    before=before,
                    after=None,
                )
            )
            return

    def _add_limitation(self, report: ResearchReport, finding: AttackFinding) -> None:
        text = "Some retrieved evidence was not fully synthesized; future runs should expand coverage."
        if text not in report.limitations:
            report.limitations.append(text)
        if any(
            action.action_type == RepairActionType.ADD
            and action.target_claim_id == "report.limitations"
            and action.patch == text
            for action in report.repair_actions
        ):
            return
        report.repair_actions.append(
            RepairAction(
                action_type=RepairActionType.ADD,
                target_claim_id="report.limitations",
                reason=finding.reason,
                patch=text,
                before=None,
                after=text,
            )
        )
