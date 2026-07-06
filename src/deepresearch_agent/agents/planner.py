from __future__ import annotations

from dataclasses import dataclass

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.schemas import (
    PlanQualityReport,
    PlanType,
    ResearchPlan,
    ResearchTask,
    TaskType,
)


@dataclass(frozen=True, slots=True)
class _SubtaskSpec:
    question: str
    depends_on: tuple[int, ...] = ()


class PlannerAgent(BaseAgent):
    name = "planner"
    supported_modes = {"template", "heuristic"}

    def __init__(self, mode: str = "heuristic") -> None:
        if mode not in self.supported_modes:
            raise ValueError(f"Unknown planner mode: {mode}")
        self.mode = mode

    async def _run(self, agent_input: object, context=None) -> ResearchPlan:
        if not isinstance(agent_input, str):
            raise TypeError("PlannerAgent.run expects a research question string.")
        return await self.plan(agent_input)

    async def plan(self, question: str) -> ResearchPlan:
        root = ResearchTask(
            question=question,
            task_type=TaskType.ROOT,
            priority=0,
            expected_evidence="Clarify the user's full research intent.",
        )
        plan_type = self.classify(question) if self.mode == "heuristic" else PlanType.GENERAL
        specs = self._build_specs(question, plan_type)
        search_tasks: list[ResearchTask] = []
        for index, spec in enumerate(specs):
            dependencies = [root.id, *(search_tasks[item].id for item in spec.depends_on)]
            search_tasks.append(
                ResearchTask(
                    question=spec.question,
                    task_type=TaskType.SEARCH,
                    parent_id=root.id,
                    dependencies=list(dict.fromkeys(dependencies)),
                    priority=index + 1,
                    expected_evidence=f"Find evidence about: {spec.question}",
                )
            )
        synthesize_task = ResearchTask(
            question=f"Synthesize evidence into a cited research answer for: {question}",
            task_type=TaskType.SYNTHESIZE,
            parent_id=root.id,
            dependencies=[task.id for task in search_tasks],
            priority=10,
            expected_evidence="Use retrieved evidence to draft report claims and sections.",
        )
        verification_task = ResearchTask(
            question=f"Verify claim-evidence alignment for: {question}",
            task_type=TaskType.VERIFY,
            parent_id=root.id,
            dependencies=[synthesize_task.id],
            priority=11,
            expected_evidence="Check unsupported claims, missing citations, and contradictions.",
        )
        repair_task = ResearchTask(
            question=f"Repair weak claims for: {question}",
            task_type=TaskType.REPAIR,
            parent_id=root.id,
            dependencies=[verification_task.id],
            priority=12,
            expected_evidence="Apply ADD, DELETE, MODIFY, or VERIFY actions when needed.",
        )
        plan = ResearchPlan(
            root_question=question,
            tasks=[root, *search_tasks, synthesize_task, verification_task, repair_task],
            rationale=(
                f"Use the {self.mode} planner for a {plan_type.value} question, gather "
                "evidence through dependency-aware subtasks, then synthesize, verify, and repair."
            ),
            plan_type=plan_type,
            sub_questions=[spec.question for spec in specs],
        )
        plan.quality_report = self.assess_quality(plan)
        return plan

    def classify(self, question: str) -> PlanType:
        lowered = question.lower()
        cue_groups = (
            (
                PlanType.COMPARISON,
                ("compare", "comparison", "versus", " vs ", "difference", "比较", "对比", "区别", "优缺点"),
            ),
            (
                PlanType.RISK_ANALYSIS,
                (
                    "risk",
                    "failure",
                    "hallucination",
                    "reliability",
                    "verification",
                    "citation",
                    "风险",
                    "故障",
                    "幻觉",
                    "可靠",
                    "验证",
                    "引用",
                ),
            ),
            (
                PlanType.SOLUTION_DESIGN,
                ("design", "architecture", "implement", "build", "how to", "方案", "架构", "实现", "如何"),
            ),
        )
        for plan_type, cues in cue_groups:
            if any(cue in lowered for cue in cues):
                return plan_type
        return PlanType.GENERAL

    def assess_quality(self, plan: ResearchPlan) -> PlanQualityReport:
        all_text = " ".join([plan.root_question, *plan.sub_questions]).lower()
        dependency_count = sum(len(task.dependencies) for task in plan.tasks)
        checks = {
            "background": any(term in all_text for term in ["background", "concept", "scope"]),
            "implementation": any(
                term in all_text for term in ["implementation", "mechanism", "architecture", "mitigation"]
            ),
            "risk": any(term in all_text for term in ["risk", "failure", "hallucination", "reliability"]),
            "evaluation": any(term in all_text for term in ["evaluation", "metric", "criteria"]),
            "tradeoffs": any(term in all_text for term in ["tradeoff", "limitation", "strength"]),
        }
        required_checks = {
            PlanType.GENERAL: set(checks),
            PlanType.COMPARISON: {"background", "evaluation", "tradeoffs"},
            PlanType.RISK_ANALYSIS: {"background", "implementation", "risk", "evaluation", "tradeoffs"},
            PlanType.SOLUTION_DESIGN: {"background", "implementation", "risk", "evaluation", "tradeoffs"},
        }[plan.plan_type]
        issues: list[str] = []
        if len(plan.tasks) < 5:
            issues.append("Plan should contain at least five tasks.")
        if dependency_count == 0:
            issues.append("Plan should expose task dependencies.")
        for name in sorted(required_checks):
            if not checks[name]:
                issues.append(f"Plan is missing required {name} coverage for {plan.plan_type.value}.")
        return PlanQualityReport(
            task_count=len(plan.tasks),
            dependency_count=dependency_count,
            has_background=checks["background"],
            has_implementation=checks["implementation"],
            has_risk=checks["risk"],
            has_evaluation=checks["evaluation"],
            has_tradeoffs=checks["tradeoffs"],
            issues=issues,
        )

    def _build_specs(self, question: str, plan_type: PlanType) -> list[_SubtaskSpec]:
        normalized = question.strip()
        if self.mode == "template":
            return self._template_specs(normalized)
        builders = {
            PlanType.COMPARISON: self._comparison_specs,
            PlanType.RISK_ANALYSIS: self._risk_specs,
            PlanType.SOLUTION_DESIGN: self._solution_specs,
            PlanType.GENERAL: self._template_specs,
        }
        return builders[plan_type](normalized)

    def _template_specs(self, question: str) -> list[_SubtaskSpec]:
        templates = [
            "What background concepts are needed to answer: {question}",
            "What implementation mechanisms are central to: {question}",
            "What reliability risks or hallucination risks appear in: {question}",
            "What evaluation metrics can measure success for: {question}",
            "What engineering tradeoffs and limitations matter for: {question}",
        ]
        return [_SubtaskSpec(template.format(question=question)) for template in templates]

    def _comparison_specs(self, question: str) -> list[_SubtaskSpec]:
        return [
            _SubtaskSpec(f"Define the compared concepts, scope, and evaluation criteria for: {question}"),
            _SubtaskSpec(f"Collect evidence about the strengths and limitations of the first option in: {question}"),
            _SubtaskSpec(f"Collect evidence about the strengths and limitations of the second option in: {question}"),
            _SubtaskSpec(
                f"Compare tradeoffs, evaluation metrics, and recommended use cases for: {question}",
                depends_on=(0, 1, 2),
            ),
        ]

    def _risk_specs(self, question: str) -> list[_SubtaskSpec]:
        return [
            _SubtaskSpec(f"Establish the background concepts and scope for: {question}"),
            _SubtaskSpec(f"Identify failure modes, reliability risks, and affected claims for: {question}"),
            _SubtaskSpec(
                f"Investigate implementation mechanisms and mitigations for: {question}",
                depends_on=(1,),
            ),
            _SubtaskSpec(
                f"Define evaluation metrics and verification criteria for: {question}",
                depends_on=(1, 2),
            ),
            _SubtaskSpec(
                f"Analyze residual tradeoffs and limitations after mitigation for: {question}",
                depends_on=(2,),
            ),
        ]

    def _solution_specs(self, question: str) -> list[_SubtaskSpec]:
        return [
            _SubtaskSpec(f"Clarify background, requirements, and constraints for: {question}"),
            _SubtaskSpec(f"Design the architecture and component responsibilities for: {question}", depends_on=(0,)),
            _SubtaskSpec(f"Detail implementation mechanisms and execution flow for: {question}", depends_on=(1,)),
            _SubtaskSpec(f"Identify reliability risks, failure modes, and limitations for: {question}"),
            _SubtaskSpec(
                f"Define evaluation metrics, acceptance criteria, and engineering tradeoffs for: {question}",
                depends_on=(2, 3),
            ),
        ]


class TemplatePlannerAgent(PlannerAgent):
    def __init__(self) -> None:
        super().__init__(mode="template")


class HeuristicPlannerAgent(PlannerAgent):
    def __init__(self) -> None:
        super().__init__(mode="heuristic")
