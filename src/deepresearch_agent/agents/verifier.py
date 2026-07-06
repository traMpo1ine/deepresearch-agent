from __future__ import annotations

import re
from typing import Any

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.schemas import (
    AtomicVerificationResult,
    Claim,
    Evidence,
    VerificationStatus,
    VerificationTrace,
)


class VerifierAgent(BaseAgent):
    name = "verifier"

    async def _run(self, agent_input: object, context=None) -> Claim:
        if not isinstance(agent_input, dict):
            raise TypeError("VerifierAgent.run expects {'claim': Claim, 'evidence': list[Evidence]}.")
        claim = agent_input.get("claim")
        evidence = agent_input.get("evidence")
        if not isinstance(claim, Claim) or not isinstance(evidence, list):
            raise TypeError("VerifierAgent.run expects {'claim': Claim, 'evidence': list[Evidence]}.")
        return await self.verify(claim, evidence)

    async def verify(self, claim: Claim, evidence: list[Evidence]) -> Claim:
        evidence_by_id = {item.id: item for item in evidence}
        cited = [evidence_by_id[cid] for cid in claim.citation_ids if cid in evidence_by_id]
        atomic_claims = self.split_atomic_claims(claim.text)
        if not cited:
            atomic_results = [
                AtomicVerificationResult(
                    text=atomic,
                    status=VerificationStatus.UNSUPPORTED,
                    support_terms=[],
                    missing_terms=sorted(self._important_terms(atomic)),
                    term_overlap=0.0,
                    quote_overlap=0.0,
                    decision_reason="No valid citation ids were attached to this atomic claim.",
                    reason="No valid citation ids were attached to this atomic claim.",
                )
                for atomic in atomic_claims
            ]
            claim.verification_status = VerificationStatus.UNSUPPORTED
            claim.confidence = min(claim.confidence, 0.25)
            claim.verification_reason = "No valid citation ids were attached to this claim."
            claim.needs_verification = True
            claim.verification_trace = VerificationTrace(
                claim_id=claim.id,
                status=claim.verification_status,
                matched_evidence_ids=[],
                support_terms=[],
                missing_terms=sorted(self._important_terms(claim.text)),
                reason=claim.verification_reason,
                citation_presence=False,
                term_overlap=0.0,
                quote_overlap=0.0,
                support_level="none",
                atomic_claims=atomic_claims,
                atomic_results=atomic_results,
            )
            return claim

        atomic_results = [self._verify_atomic(atomic, cited) for atomic in atomic_claims]
        claim_terms = set().union(*(set(result.support_terms) | set(result.missing_terms) for result in atomic_results))
        support_terms = sorted({term for result in atomic_results for term in result.support_terms})
        missing_terms = sorted({term for result in atomic_results for term in result.missing_terms})
        ratio = sum(result.term_overlap for result in atomic_results) / max(len(atomic_results), 1)
        contradiction_cues = sorted({cue for result in atomic_results for cue in result.contradiction_cues})
        quote_overlap = sum(result.quote_overlap for result in atomic_results) / max(len(atomic_results), 1)
        claim.matched_evidence_ids = [item.id for item in cited]
        claim.missing_terms = missing_terms
        claim.verification_reason = (
            f"Matched {len(support_terms)}/{len(claim_terms)} important terms; "
            f"missing={missing_terms[:5]}."
        )
        claim.verification_status = self._aggregate_atomic_status(atomic_results)
        if claim.verification_status == VerificationStatus.CONTRADICTED:
            claim.confidence = min(claim.confidence, 0.20)
            claim.needs_verification = True
            claim.verification_reason += " Potential contradiction cue detected."
        elif claim.verification_status == VerificationStatus.SUPPORTED:
            claim.confidence = max(claim.confidence, 0.75)
            claim.needs_verification = False
        elif claim.verification_status == VerificationStatus.PARTIAL:
            claim.confidence = min(max(claim.confidence, 0.45), 0.65)
            claim.needs_verification = True
        else:
            claim.confidence = min(claim.confidence, 0.30)
            claim.needs_verification = True
        claim.verification_trace = VerificationTrace(
            claim_id=claim.id,
            status=claim.verification_status,
            matched_evidence_ids=claim.matched_evidence_ids,
            support_terms=support_terms,
            missing_terms=missing_terms,
            reason=claim.verification_reason,
            citation_presence=True,
            term_overlap=ratio,
            quote_overlap=quote_overlap,
            contradiction_cues=contradiction_cues,
            support_level=claim.verification_status.value,
            atomic_claims=atomic_claims,
            atomic_results=atomic_results,
        )
        return claim

    def _verify_atomic(self, atomic_claim: str, cited: list[Evidence]) -> AtomicVerificationResult:
        terms = self._important_terms(atomic_claim)
        scored = [self._score_evidence(atomic_claim, terms, item) for item in cited]
        scored.sort(key=lambda item: item["score"], reverse=True)
        best = scored[0] if scored else None
        best_evidence = best["evidence"] if best else None
        evidence_text = self._evidence_text(best_evidence).lower() if best_evidence else ""
        support_terms = sorted(term for term in terms if term in evidence_text)
        missing_terms = sorted(term for term in terms if term not in evidence_text)
        term_overlap = len(support_terms) / max(len(terms), 1)
        quote_overlap = float(best["quote_overlap"]) if best else 0.0
        contradiction_cues = self._contradiction_cues(atomic_claim, evidence_text)
        if contradiction_cues:
            status = VerificationStatus.CONTRADICTED
        elif term_overlap >= 0.35:
            status = VerificationStatus.SUPPORTED
        elif term_overlap > 0:
            status = VerificationStatus.PARTIAL
        else:
            status = VerificationStatus.UNSUPPORTED
        return AtomicVerificationResult(
            text=atomic_claim,
            status=status,
            support_terms=support_terms,
            missing_terms=missing_terms,
            term_overlap=term_overlap,
            quote_overlap=quote_overlap,
            contradiction_cues=contradiction_cues,
            evidence_id=best_evidence.id if best_evidence else None,
            best_quote=best_evidence.quote if best_evidence else None,
            decision_reason=(
                f"Best evidence={best_evidence.id if best_evidence else 'none'}; "
                f"term_overlap={term_overlap:.2f}; quote_overlap={quote_overlap:.2f}; "
                f"contradiction_cues={contradiction_cues}."
            ),
            evidence_scores=[
                {
                    "evidence_id": str(item["evidence"].id),
                    "term_overlap": float(item["term_overlap"]),
                    "quote_overlap": float(item["quote_overlap"]),
                    "source_trust": float(item["source_trust"]),
                    "score": float(item["score"]),
                }
                for item in scored
            ],
            reason=(
                f"Atomic claim matched {len(support_terms)}/{len(terms)} important terms; "
                f"status={status.value}."
            ),
        )

    def _aggregate_atomic_status(
        self,
        atomic_results: list[AtomicVerificationResult],
    ) -> VerificationStatus:
        statuses = [result.status for result in atomic_results]
        if not statuses:
            return VerificationStatus.UNSUPPORTED
        if VerificationStatus.CONTRADICTED in statuses:
            return VerificationStatus.CONTRADICTED
        if all(status == VerificationStatus.SUPPORTED for status in statuses):
            return VerificationStatus.SUPPORTED
        if all(status == VerificationStatus.UNSUPPORTED for status in statuses):
            return VerificationStatus.UNSUPPORTED
        return VerificationStatus.PARTIAL

    def _important_terms(self, text: str) -> set[str]:
        stopwords = {
            "should",
            "while",
            "with",
            "that",
            "this",
            "from",
            "into",
            "and",
            "the",
            "can",
            "important",
        }
        terms = {
            term.lower()
            for term in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", text)
            if len(term) > 4 and term.lower() not in stopwords
        }
        terms.update(re.findall(r"[\u4e00-\u9fff]{2,}", text))
        return terms

    def _score_evidence(
        self,
        atomic_claim: str,
        terms: set[str],
        evidence: Evidence,
    ) -> dict[str, Any]:
        evidence_text = self._evidence_text(evidence).lower()
        term_overlap = (
            sum(1 for term in terms if term in evidence_text) / max(len(terms), 1)
        )
        quote_overlap = self._quote_overlap(atomic_claim, [evidence])
        source_trust = self._source_trust(evidence)
        return {
            "evidence": evidence,
            "term_overlap": term_overlap,
            "quote_overlap": quote_overlap,
            "source_trust": source_trust,
            "score": term_overlap * 0.65 + quote_overlap * 0.25 + source_trust * 0.10,
        }

    def _evidence_text(self, evidence: Evidence) -> str:
        return f"{evidence.title} {evidence.text} {evidence.quote or ''}"

    def _source_trust(self, evidence: Evidence) -> float:
        raw = str(evidence.metadata.get("trust_level", "medium")).lower()
        return {"high": 1.0, "medium": 0.7, "low": 0.4}.get(raw, 0.7)

    def _contradiction_cues(self, claim_text: str, evidence_text: str) -> list[str]:
        claim_lower = claim_text.lower()
        contradiction_pairs = [
            ("always", "not always"),
            ("never", "can"),
            ("must", "optional"),
            ("guarantees", "does not guarantee"),
            ("guarantee", "does not guarantee"),
            ("eliminate", "reduce"),
            ("all", "some"),
            ("only", "also"),
            ("不需要", "需要"),
            ("总是", "不一定"),
            ("必须", "可选"),
            ("完全", "降低"),
            ("全部", "部分"),
        ]
        cues = [
            f"{left} vs {right}"
            for left, right in contradiction_pairs
            if left in claim_lower and right in evidence_text
        ]
        absolute_terms = {
            "always",
            "never",
            "all",
            "completely",
            "guarantees",
            "guarantee",
            "完全",
            "总是",
            "全部",
        }
        hedge_terms = {
            "may",
            "can",
            "some",
            "often",
            "reduce",
            "not always",
            "可能",
            "部分",
            "降低",
            "不一定",
        }
        if any(term in claim_lower for term in absolute_terms) and any(
            term in evidence_text for term in hedge_terms
        ):
            cues.append("absolute claim vs hedged evidence")
        claim_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", claim_lower))
        evidence_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", evidence_text))
        if claim_numbers and evidence_numbers and claim_numbers.isdisjoint(evidence_numbers):
            cues.append(
                f"quantity mismatch: claim={sorted(claim_numbers)} evidence={sorted(evidence_numbers)}"
            )
        return sorted(set(cues))

    def _quote_overlap(self, claim_text: str, cited: list[Evidence]) -> float:
        claim_terms = self._important_terms(claim_text)
        quote_terms = self._important_terms(" ".join(item.quote or "" for item in cited))
        if not claim_terms:
            return 0.0
        return len(claim_terms & quote_terms) / len(claim_terms)

    def split_atomic_claims(self, text: str) -> list[str]:
        pieces = re.split(r"\b(?:and|while|because|;)\b|[。；;]", text)
        return [piece.strip(" .") for piece in pieces if piece.strip(" .")]
