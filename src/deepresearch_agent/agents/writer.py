from __future__ import annotations

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.claim_preflight import ClaimPreflight
from deepresearch_agent.schemas import (
    Claim,
    CompressedContext,
    Evidence,
    PlanType,
    ReportSection,
    ResearchReport,
)


class WriterAgent(BaseAgent):
    name = "writer"

    async def _run(self, agent_input: object, context=None) -> ResearchReport:
        if not isinstance(agent_input, dict):
            raise TypeError(
                "WriterAgent.run expects {'question': str, 'evidence': list[Evidence], "
                "'context': CompressedContext | None, 'plan_type': PlanType}."
            )
        question = agent_input.get("question")
        evidence = agent_input.get("evidence")
        compressed_context = agent_input.get("context")
        plan_type = agent_input.get("plan_type", PlanType.GENERAL)
        if not isinstance(question, str) or not isinstance(evidence, list):
            raise TypeError("WriterAgent.run expects a question string and evidence list.")
        return await self.write(question, evidence, compressed_context, plan_type)

    async def write(
        self,
        question: str,
        evidence: list[Evidence],
        context: CompressedContext | None = None,
        plan_type: PlanType = PlanType.GENERAL,
    ) -> ResearchReport:
        ranked = sorted(evidence, key=lambda item: item.score, reverse=True)
        context_text = context.to_text() if context else "\n".join(item.quote or item.text for item in ranked[:4])
        claims = self._claims(ranked, plan_type)
        preflight = ClaimPreflight().run(claims, ranked)
        sections = self._sections(plan_type, claims)
        if context_text:
            sections.append(
                ReportSection(
                    title="Compressed Evidence Snapshot",
                    body=context_text[:1200],
                    claim_ids=[],
                )
            )
        summary = self._summary(plan_type)
        limitations = [
            "This offline v1 uses deterministic local retrieval and heuristic verification.",
            "Real LLM backends are adapter-ready but should be enabled only after the offline pipeline is stable.",
            *preflight.limitations,
        ]
        report = ResearchReport(
            question=question,
            title=self._title(plan_type),
            summary=summary,
            claims=claims,
            evidence=ranked,
            sections=sections,
            limitations=limitations,
        )
        report.run_summary["claim_preflight"] = {
            "duplicate_claim_ids": preflight.duplicate_claim_ids,
            "conflict_evidence_ids": preflight.conflict_evidence_ids,
            "downgraded_claim_ids": preflight.downgraded_claim_ids,
        }
        return report

    def _title(self, plan_type: PlanType) -> str:
        titles = {
            PlanType.COMPARISON: "DeepResearch Agent Comparison Report",
            PlanType.RISK_ANALYSIS: "DeepResearch Agent Risk Analysis Report",
            PlanType.SOLUTION_DESIGN: "DeepResearch Agent Solution Design Report",
            PlanType.GENERAL: "DeepResearch Agent Offline Research Report",
        }
        return titles[plan_type]

    def _summary(self, plan_type: PlanType) -> str:
        summaries = {
            PlanType.COMPARISON: (
                "This report compares alternatives by defining the decision criteria, "
                "summarizing tradeoffs, and grounding the recommendation in retrieved evidence."
            ),
            PlanType.RISK_ANALYSIS: (
                "This report treats the question as a reliability problem: it identifies "
                "failure modes, mitigation mechanisms, verification signals, and remaining limitations."
            ),
            PlanType.SOLUTION_DESIGN: (
                "This report turns the question into an implementation plan, connecting goals, "
                "modules, data flow, evaluation, and engineering tradeoffs."
            ),
            PlanType.GENERAL: (
                "A credible DeepResearch Agent should be engineered as an inspectable pipeline: "
                "planning creates task structure, retrieval and memory provide evidence, "
                "compression keeps useful context, and verification plus repair reduce unsupported claims."
            ),
        }
        return summaries[plan_type]

    def _sections(self, plan_type: PlanType, claims: list[Claim]) -> list[ReportSection]:
        section_specs = {
            PlanType.COMPARISON: [
                (
                    "Comparison Frame",
                    "The answer should first define the compared options and the criteria used to judge them.",
                    [claims[0].id],
                ),
                (
                    "Tradeoffs and Recommendation",
                    "The synthesis should separate strengths, limitations, and suitable use cases before making a cautious recommendation.",
                    [claims[1].id, claims[2].id],
                ),
            ],
            PlanType.RISK_ANALYSIS: [
                (
                    "Failure Modes",
                    "The answer should identify how research agents can fail through missing evidence, weak citations, or hidden contradictions.",
                    [claims[0].id],
                ),
                (
                    "Mitigation and Verification",
                    "The system should make reliability mechanisms observable through verifier traces, citation checks, and repair actions.",
                    [claims[1].id, claims[2].id],
                ),
            ],
            PlanType.SOLUTION_DESIGN: [
                (
                    "Architecture",
                    "The answer should connect the user goal to planner, retrieval, memory, compression, writer, verifier, and repair modules.",
                    [claims[0].id],
                ),
                (
                    "Execution and Evaluation",
                    "The implementation should preserve dependency order, keep traces, and evaluate whether generated claims are grounded.",
                    [claims[1].id, claims[2].id],
                ),
            ],
            PlanType.GENERAL: [
                (
                    "System Design",
                    "The offline pipeline decomposes the research question, retrieves local evidence, compresses context, writes cited claims, and verifies the claim-evidence relation.",
                    [claims[0].id],
                ),
                (
                    "Reliability Mechanisms",
                    "Citation tracking, verifier traces, and Red-Blue repair actions make failure modes visible instead of hiding them inside a final answer.",
                    [claims[1].id, claims[2].id],
                ),
            ],
        }
        return [
            ReportSection(title=title, body=body, claim_ids=claim_ids)
            for title, body, claim_ids in section_specs[plan_type]
        ]

    def _claims(self, evidence: list[Evidence], plan_type: PlanType) -> list[Claim]:
        claim_specs = {
            PlanType.COMPARISON: [
                (
                    "SQLite and vector retrieval solve different parts of an agent memory problem.",
                    "sqlite vector retrieval different parts agent memory problem",
                    0.68,
                ),
                (
                    "SQLite is strong for durable records, relational queries, audit trails, and exact traceability.",
                    "sqlite durable records relational queries audit trails exact traceability",
                    0.66,
                ),
                (
                    "Vector retrieval is strong for semantic similarity, fuzzy recall, and reusing evidence across related queries.",
                    "vector retrieval semantic similarity fuzzy recall reusing evidence related queries",
                    0.66,
                ),
            ],
            PlanType.RISK_ANALYSIS: [
                (
                    "DeepResearch Agents can fail when claims are not grounded in inspectable evidence.",
                    "hallucination unsupported claims evidence citation contradiction missing",
                    0.70,
                ),
                (
                    "Citation tracking helps connect each important claim to a concrete source chunk and quote span.",
                    "citation evidence source chunk quote verifier audit",
                    0.70,
                ),
                (
                    "Verifier and Red-Blue repair loops make weak support visible and provide explicit ADD, DELETE, MODIFY, or VERIFY actions.",
                    "verifier red blue repair add delete modify verify weak unsupported",
                    0.68,
                ),
            ],
            PlanType.SOLUTION_DESIGN: [
                (
                    "A DeepResearch Agent should expose planning, retrieval, memory, writing, verification, and repair as separate modules.",
                    "planner retrieval memory writer verifier repair agent modules",
                    0.70,
                ),
                (
                    "A DAG coordinator with asyncio and semaphores can run independent research tasks concurrently while preserving dependency order.",
                    "dag asyncio semaphore dependency concurrent topological",
                    0.68,
                ),
                (
                    "Evaluation should combine citation coverage, hallucination checks, judge scores, confidence intervals, and failure analysis.",
                    "evaluation citation hallucination judge bootstrap confidence failure",
                    0.66,
                ),
            ],
            PlanType.GENERAL: [
                (
                    "DeepResearch Agent should bind important claims to inspectable evidence and source chunks.",
                    "citation evidence source chunk",
                    0.70,
                ),
                (
                    "A DAG coordinator with asyncio and semaphores can run independent research tasks concurrently while preserving dependency order.",
                    "dag asyncio semaphore dependency concurrent",
                    0.68,
                ),
                (
                    "A Red-Blue repair loop can improve reliability by detecting weak claims and applying ADD, DELETE, MODIFY, or VERIFY actions.",
                    "red blue repair add delete modify verify",
                    0.66,
                ),
            ],
        }
        return [
            self._claim(text=text, evidence=evidence, hint=hint, confidence=confidence)
            for text, hint, confidence in claim_specs[plan_type]
        ]

    def _claim(self, text: str, evidence: list[Evidence], hint: str, confidence: float) -> Claim:
        citation_ids = self._pick_citation(evidence, hint)
        return Claim(
            text=text,
            citation_ids=citation_ids[:1],
            confidence=confidence,
            needs_verification=not citation_ids,
        )

    def _pick_citation(self, evidence: list[Evidence], hint: str) -> list[str]:
        hint_terms = {term for term in hint.lower().split() if len(term) > 3}
        ranked = sorted(
            evidence,
            key=lambda item: (
                sum(
                    1
                    for term in hint_terms
                    if term in f"{item.title} {item.text} {item.quote or ''}".lower()
                ),
                item.score,
            ),
            reverse=True,
        )
        return [ranked[0].id] if ranked else []
