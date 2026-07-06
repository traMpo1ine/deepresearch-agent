from __future__ import annotations

from deepresearch_agent.orchestration.dag import DAGTaskGraph
from deepresearch_agent.schemas import ResearchPlan, ResearchTask


def plan_to_mermaid(tasks: list[ResearchTask]) -> str:
    lines = ["flowchart TD"]
    for task in tasks:
        label = f"{task.task_type.value}: {task.question}".replace('"', "'")
        lines.append(f'    {task.id}["{label}"]')
    for task in tasks:
        for dep_id in task.dependencies:
            lines.append(f"    {dep_id} --> {task.id}")
    return "\n".join(lines)


def plan_overview(plan: ResearchPlan) -> dict:
    graph = DAGTaskGraph(plan.tasks)
    return {
        "root_question": plan.root_question,
        "plan_type": plan.plan_type.value,
        "task_count": len(plan.tasks),
        "dependency_count": sum(len(task.dependencies) for task in plan.tasks),
        "topological_batches": [
            [task.id for task in batch]
            for batch in graph.topological_batches()
        ],
        "tasks": [
            {
                "id": task.id,
                "type": task.task_type.value,
                "question": task.question,
                "dependencies": task.dependencies,
                "expected_evidence": task.expected_evidence,
            }
            for task in plan.tasks
        ],
        "quality_report": plan.quality_report,
        "mermaid": plan_to_mermaid(plan.tasks),
    }


def plan_to_markdown(plan: ResearchPlan) -> str:
    overview = plan_overview(plan)
    lines = [
        "# Plan Inspection",
        "",
        f"Question: {plan.root_question}",
        "",
        "## Summary",
        "",
        f"- tasks: {overview['task_count']}",
        f"- dependencies: {overview['dependency_count']}",
        f"- batches: {len(overview['topological_batches'])}",
        f"- plan type: {overview['plan_type']}",
        "",
        "## Topological Batches",
        "",
    ]
    id_to_task = {task.id: task for task in plan.tasks}
    for index, batch in enumerate(overview["topological_batches"], start=1):
        names = ", ".join(f"{task_id} ({id_to_task[task_id].task_type.value})" for task_id in batch)
        lines.append(f"- Batch {index}: {names}")
    lines.extend(["", "## Tasks", ""])
    for task in plan.tasks:
        deps = ", ".join(task.dependencies) if task.dependencies else "none"
        lines.extend(
            [
                f"### {task.id}",
                "",
                f"- type: {task.task_type.value}",
                f"- dependencies: {deps}",
                f"- question: {task.question}",
                f"- expected evidence: {task.expected_evidence}",
                "",
            ]
        )
    lines.extend(["## Mermaid", "", "```mermaid", overview["mermaid"], "```"])
    return "\n".join(lines)
