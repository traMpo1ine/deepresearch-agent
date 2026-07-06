from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ResumeEvidence:
    """A resume bullet backed by code paths, tests, commands, artifacts, and caveats."""

    evidence_id: str
    resume_bullet: str
    code_paths: list[str]
    tests: list[str]
    commands: list[str]
    artifacts: list[str]
    learning_story: str
    boundary: str

    def to_dict(self) -> dict:
        return asdict(self)


RESUME_EVIDENCE: tuple[ResumeEvidence, ...] = (
    ResumeEvidence(
        evidence_id="orchestration",
        resume_bullet=(
            "手写 Planner/DAGTaskGraph/TaskStateMachine/Coordinator，将复杂研究问题拆解为"
            "多 Agent 任务图，并使用 asyncio + Semaphore 执行拓扑批次任务；9 状态状态机"
            "记录 timeout、retry、replan 和 fallback trace。"
        ),
        code_paths=[
            "src/deepresearch_agent/agents/planner.py",
            "src/deepresearch_agent/orchestration/dag.py",
            "src/deepresearch_agent/orchestration/state_machine.py",
            "src/deepresearch_agent/orchestration/coordinator.py",
            "src/deepresearch_agent/agents/base.py",
        ],
        tests=[
            "tests/unit/test_planner.py",
            "tests/unit/test_dag.py",
            "tests/unit/test_state_machine.py",
            "tests/unit/test_agent_run_interface.py",
            "tests/integration/test_mock_pipeline.py",
            "tests/unit/test_v3_mechanisms.py",
        ],
        commands=[
            'uv run python scripts/inspect_plan.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic',
            "uv run python scripts/inspect_orchestration_failure.py --case batch_replan",
            'uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？"',
        ],
        artifacts=[
            "reports/showcase/final_check/plan.md",
            "reports/showcase/final_check/run_summary.json",
            "reports/showcase/final_check/memory.sqlite3",
            "docs/generated/day09_orchestration_failure_trace.md",
        ],
        learning_story=(
            "最初顺序 pipeline 难以表达复杂依赖，所以先手写 DAG 和状态机；后续又把"
            "BaseAgent.run 接进 Coordinator，让真实运行也能留下 AgentResult trace。"
        ),
        boundary=(
            "当前是离线研究任务编排，不是分布式调度系统；并发粒度是同层任务，而不是跨机器任务队列。"
        ),
    ),
    ResumeEvidence(
        evidence_id="memory_vector",
        resume_bullet=(
            "构建 SQLite 共享记忆与 numpy hashing vector index，结构化保存运行轨迹，"
            "实现 claim -> citation -> source chunk -> quote span 的可追溯链路。"
        ),
        code_paths=[
            "src/deepresearch_agent/memory/sqlite_store.py",
            "src/deepresearch_agent/memory/vector_index.py",
            "scripts/inspect_memory.py",
            "scripts/inspect_report_trace.py",
        ],
        tests=[
            "tests/unit/test_sqlite_memory.py",
            "tests/unit/test_vector_index.py",
            "tests/unit/test_inspect_memory_script.py",
            "tests/unit/test_inspect_report_trace.py",
        ],
        commands=[
            "uv run python scripts/inspect_memory.py --memory-path reports/showcase/final_check/memory.sqlite3 --schema --runs --limit 5",
            "uv run python scripts/inspect_report_trace.py --report-json reports/showcase/final_check/report.json",
        ],
        artifacts=[
            "reports/showcase/final_check/memory_trace.md",
            "reports/showcase/final_check/report.json",
            "reports/showcase/final_check/memory.sqlite3",
        ],
        learning_story=(
            "SQLite 负责审计链路，numpy index 只负责相似召回。两者分离后，即使以后换成"
            "FAISS/Chroma，claim/evidence/report 的可追溯记录也不需要重写。"
        ),
        boundary=(
            "hashing vectorizer 是离线可解释 baseline，不代表大模型 embedding 的真实语义能力。"
        ),
    ),
    ResumeEvidence(
        evidence_id="compression",
        resume_bullet=(
            "设计 TextRank 上下文压缩与引用保护机制，通过 L1 向量粗筛、L2 TextRank 句子排序、"
            "L3 citation quote 保留，降低上下文长度同时保留可验证证据。"
        ),
        code_paths=[
            "src/deepresearch_agent/compression/textrank.py",
            "scripts/inspect_compression.py",
            "data/examples/compression_cases.jsonl",
        ],
        tests=[
            "tests/unit/test_compression.py",
            "tests/unit/test_compression_cases.py",
        ],
        commands=[
            "uv run python scripts/inspect_compression.py --case quote_preservation",
            "uv run python scripts/inspect_compression.py --case multi_quote_preservation --json",
        ],
        artifacts=[
            "reports/showcase/final_check/compression_trace.md",
            "docs/generated/day05_compression_trace.md",
        ],
        learning_story=(
            "普通摘要可能改写或丢掉引用原文，所以压缩不是只追求短，而是要保护后续 Verifier "
            "需要的 quote。"
        ),
        boundary=(
            "TextRank 是轻量启发式压缩，不保证覆盖所有关键信息；复杂任务后续可接 LLM compressor 做对照。"
        ),
    ),
    ResumeEvidence(
        evidence_id="verifier_redblue",
        resume_bullet=(
            "实现 Verifier + Red-Blue 对抗修复：Verifier 将长 claim 拆成 atomic claims 并输出"
            "多维 VerificationTrace；Blue Agent 执行 ADD/DELETE/MODIFY/VERIFY，并记录 repair loop "
            "收敛、震荡和最大轮数停止原因。"
        ),
        code_paths=[
            "src/deepresearch_agent/agents/verifier.py",
            "src/deepresearch_agent/agents/critic.py",
            "src/deepresearch_agent/redblue/blue_agent.py",
            "src/deepresearch_agent/redblue_convergence.py",
            "scripts/inspect_verification.py",
            "scripts/inspect_redblue.py",
            "scripts/inspect_redblue_convergence.py",
        ],
        tests=[
            "tests/unit/test_verifier.py",
            "tests/unit/test_verification_cases.py",
            "tests/unit/test_redblue.py",
            "tests/unit/test_redblue_cases.py",
            "tests/unit/test_redblue_fixtures.py",
        ],
        commands=[
            "uv run python scripts/inspect_verification.py --case mixed_atomic",
            "uv run python scripts/inspect_redblue.py --case overclaim",
            "uv run python scripts/inspect_redblue_convergence.py --case oscillation",
            "uv run python scripts/inspect_redblue.py --case omission --json",
        ],
        artifacts=[
            "reports/showcase/final_check/verifier_trace.md",
            "reports/showcase/final_check/redblue_trace.md",
            "docs/generated/day03_verifier_trace.md",
            "docs/generated/day04_redblue_trace.md",
            "docs/generated/day10_redblue_convergence_trace.md",
        ],
        learning_story=(
            "先做 fixed cases 和可观察 trace，再深化算法。这样可以在不依赖真实 LLM 的情况下，"
            "稳定解释每个 claim 为什么 supported/partial/unsupported/contradicted。"
        ),
        boundary=(
            "当前 verifier 是 heuristic，不是严格 NLI；Red-Blue repair 仍可能残留过度概括或旧记忆问题。"
        ),
    ),
    ResumeEvidence(
        evidence_id="structured_preflight",
        resume_bullet=(
            "设计三层 JSON fallback 与 Claim Preflight：对 fenced/坏格式/缺字段 JSON 执行"
            "结构化解析恢复，并在 Writer 前做重复 claim、冲突 evidence 和过强断言的轻量消解。"
        ),
        code_paths=[
            "src/deepresearch_agent/structured_output.py",
            "src/deepresearch_agent/claim_preflight.py",
            "scripts/inspect_structured_output.py",
            "src/deepresearch_agent/agents/writer.py",
        ],
        tests=[
            "tests/unit/test_structured_output.py",
            "tests/unit/test_claim_preflight.py",
            "tests/unit/test_writer.py",
        ],
        commands=[
            "uv run python scripts/inspect_structured_output.py --summary",
            "uv run python scripts/inspect_structured_output.py --case combo_repair_001",
        ],
        artifacts=[
            "data/examples/structured_output_cases.jsonl",
            "docs/generated/day12_structured_output_trace.md",
            "docs/learning_structured_output_fallback.md",
            "docs/learning_claim_preflight.md",
        ],
        learning_story=(
            "真实 LLM 输出经常带代码块、前后解释文本或轻微坏 JSON，所以先做可测试的三层 fallback；"
            "同时在 Writer 前做轻量 claim preflight，把明显重复、冲突提示和过强表达提前暴露。"
        ),
        boundary=(
            "JSON fallback 只覆盖常见坏格式；Claim Preflight 是启发式写前防御，不替代 Verifier/NLI。"
        ),
    ),
    ResumeEvidence(
        evidence_id="evaluation",
        resume_bullet=(
            "自建 35 题 ResearchBench-style 离线评测集、10 题 adversarial suite、60 题 extended coverage "
            "和 80 条 Red-Blue fixtures，"
            "覆盖 11 个 domain 和 HotpotQA-style 多跳子集；60 题 ablation 中 baseline judge mean 0.764 -> "
            "full 0.880，weak_support_rate 1.000 -> 0.431，full repair_precision 0.944。"
        ),
        code_paths=[
            "src/deepresearch_agent/evaluation/runner.py",
            "src/deepresearch_agent/evaluation/metrics.py",
            "scripts/run_eval.py",
            "scripts/run_redblue_eval.py",
            "scripts/inspect_resume_metrics.py",
            "configs/default.toml",
        ],
        tests=[
            "tests/unit/test_evaluation_runner.py",
            "tests/unit/test_evaluation_cases.py",
            "tests/unit/test_redblue_fixture_eval.py",
            "tests/unit/test_extended_benchmark.py",
            "tests/unit/test_completion_check.py",
        ],
        commands=[
            "uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue,full",
            "uv run python scripts/run_eval.py --config configs/default.toml --group-by domain",
            "uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue",
            "uv run python scripts/run_redblue_eval.py",
            "uv run python scripts/inspect_resume_metrics.py --json",
            "uv run python scripts/check_project_completion.py",
        ],
        artifacts=[
            "data/benchmarks/researchbench_extended.jsonl",
            "reports/experiments/20260702_162345_148429_researchbench_21c535de/summary.md",
            "reports/experiments/20260702_162345_148429_researchbench_21c535de/metrics.json",
            "reports/experiments/20260702_163315_852511_adversarial_f47f9b96/summary.md",
            "reports/experiments/20260702_163315_852511_adversarial_f47f9b96/metrics.json",
            "reports/experiments/20260705_020934_092414_researchbench_263e905e/summary.md",
            "reports/experiments/20260705_020934_092414_researchbench_263e905e/metrics.json",
            "reports/final/pre_resume_evidence_pack/index.md",
            "reports/final/pre_resume_evidence_pack/manifest.json",
            "docs/EXPERIMENTS.md",
        ],
        learning_story=(
            "评测先离线可复现，再做配置化实验和 integrity checks；所有数字只在同一 mock benchmark "
            "内比较，避免把离线指标包装成线上效果。"
        ),
        boundary=(
            "35 题主集仍是历史冻结对比；60 题 extended ablation 是 offline/mock 指标，未把真实 DeepSeek 输出混入主指标。"
        ),
    ),
    ResumeEvidence(
        evidence_id="corpus_profiles",
        resume_bullet=(
            "构建 local corpus profile 知识库模式，将本地 Markdown/TXT/HTML 资料构建为"
            "Searcher-compatible JSONL，并在 Web Demo 中选择不同知识库 profile。"
        ),
        code_paths=[
            "src/deepresearch_agent/corpus_profiles.py",
            "src/deepresearch_agent/agents/searcher.py",
            "src/deepresearch_agent/web/app.py",
            "src/deepresearch_agent/web/static/app.js",
            "scripts/build_corpus_profiles.py",
        ],
        tests=[
            "tests/unit/test_corpus_profiles.py",
            "tests/integration/test_web_demo.py",
        ],
        commands=[
            "uv run python scripts/build_corpus_profiles.py",
            'uv run python scripts/run_showcase.py "如何把 DeepResearch Agent 写进 AI 应用实习简历？" --corpus-path data/corpus/profiles/resume_agent_docs.jsonl',
            "uv run pytest tests/unit/test_corpus_profiles.py tests/integration/test_web_demo.py",
        ],
        artifacts=[
            "data/corpus_profiles/offline_agent_docs/agent_reliability.md",
            "data/corpus_profiles/resume_agent_docs/resume_story.md",
            "data/corpus_profiles/paper_reading_docs/paper_reading_workflow.md",
            "data/corpus/profiles/offline_agent_docs.jsonl",
            "data/corpus/profiles/resume_agent_docs.jsonl",
            "data/corpus/profiles/paper_reading_docs.jsonl",
        ],
        learning_story=(
            "为了增强 RAG/AI 应用真实感，先做稳定的本地知识库 profile，而不是不稳定的全网搜索；"
            "这样面试现场能稳定展示 chunk、citation 和 quote。"
        ),
        boundary=(
            "当前是本地资料目录构建，不是线上上传、多租户知识库或全网搜索。"
        ),
    ),
    ResumeEvidence(
        evidence_id="llm_verifier_smoke",
        resume_bullet=(
            "新增 formal LLM verifier benchmark，以 claim + evidence + quote 调用 DeepSeek 二级判断，"
            "360 次真实判断 accuracy 0.842、macro-F1 0.831，并记录 token usage 和估算成本。"
        ),
        code_paths=[
            "src/deepresearch_agent/evaluation/llm_verifier_smoke.py",
            "src/deepresearch_agent/evaluation/verifier_benchmark.py",
            "src/deepresearch_agent/structured_output.py",
            "src/deepresearch_agent/llm/openai_compatible.py",
            "scripts/run_llm_verifier_smoke.py",
            "scripts/run_formal_verifier_benchmark.py",
            "scripts/build_llm_verifier_extended_cases.py",
        ],
        tests=[
            "tests/unit/test_llm_verifier_smoke.py",
            "tests/unit/test_formal_verifier_benchmark.py",
        ],
        commands=[
            "uv run python scripts/run_llm_verifier_smoke.py --json",
            "uv run python scripts/run_llm_verifier_smoke.py --run-real --limit 10 --json",
            "uv run python scripts/run_formal_verifier_benchmark.py --run-real --model deepseek-v4-flash --repetitions 3",
            "uv run pytest tests/unit/test_llm_verifier_smoke.py",
        ],
        artifacts=[
            "data/examples/llm_verifier_cases.jsonl",
            "data/examples/llm_verifier_cases_extended.jsonl",
            "reports/llm_verifier_smoke.md",
            "reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/report.md",
            "reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/aggregate.json",
        ],
        learning_story=(
            "heuristic verifier 可解释但不等于语义蕴含判断，所以加一个可重复的 LLM 二级判断实验；"
            "它证明 provider 接入、判断格式和成本边界，不污染端到端离线指标。"
        ),
        boundary=(
            "真实调用必须显式 --run-real。该结果是 verifier 分类 benchmark，不能写成生产级 NLI 或端到端 DeepResearch 分数。"
        ),
    ),
    ResumeEvidence(
        evidence_id="demo_app",
        resume_bullet=(
            "构建 FastAPI + 静态前端本地 Demo，支持默认 evidence pack 展示、新问题 mock/offline run、"
            "状态轮询，以及报告、证据、验证、修复链路可视化。"
        ),
        code_paths=[
            "src/deepresearch_agent/web/app.py",
            "src/deepresearch_agent/web/static/index.html",
            "src/deepresearch_agent/web/static/app.js",
            "scripts/run_demo_server.py",
        ],
        tests=[
            "tests/integration/test_web_demo.py",
        ],
        commands=[
            "uv sync --extra web --extra dev",
            "uv run python scripts/run_demo_server.py",
            "uv run pytest tests/integration/test_web_demo.py",
        ],
        artifacts=[
            "reports/final/final_sprint_check/showcase/index.md",
            "reports/final/final_sprint_check/showcase/report.json",
            "reports/final/final_sprint_check/showcase/verifier_trace.md",
            "reports/final/final_sprint_check/showcase/redblue_trace.md",
        ],
        learning_story=(
            "底层 Agent 链路稳定后，用薄 Web 层把现有 showcase 产物变成可演示应用；"
            "默认 evidence pack 保证面试现场稳定，新问题 mock run 展示系统可运行。"
        ),
        boundary=(
            "这是本地作品展示，不是线上多用户服务；demo run 状态保存在进程内存中，重启后清空。"
        ),
    ),
)


def list_resume_evidence() -> list[ResumeEvidence]:
    return list(RESUME_EVIDENCE)


def get_resume_evidence(evidence_id: str) -> ResumeEvidence:
    for entry in RESUME_EVIDENCE:
        if entry.evidence_id == evidence_id:
            return entry
    valid = ", ".join(entry.evidence_id for entry in RESUME_EVIDENCE)
    raise KeyError(f"Unknown resume evidence id: {evidence_id}. Valid ids: {valid}")


def build_resume_evidence_payload(
    evidence_id: str | None = None,
    root: Path | None = None,
) -> dict:
    entries = [get_resume_evidence(evidence_id)] if evidence_id else list_resume_evidence()
    payload_entries = []
    project_root = root or Path.cwd()
    for entry in entries:
        item = entry.to_dict()
        item["path_checks"] = [
            {"path": path, "exists": (project_root / path).exists()}
            for path in [*entry.code_paths, *entry.tests, *entry.artifacts]
        ]
        payload_entries.append(item)
    return {
        "count": len(payload_entries),
        "entries": payload_entries,
    }


def payload_to_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def payload_to_markdown(payload: dict) -> str:
    lines = [
        "# Resume Evidence Traceability",
        "",
        "这份输出把每条可写进简历的说法，映射到代码、测试、命令、实验产物和边界。",
        "",
    ]
    for entry in payload["entries"]:
        lines.extend(
            [
                f"## {entry['evidence_id']}",
                "",
                f"**Resume bullet:** {entry['resume_bullet']}",
                "",
                "**Code paths:**",
            ]
        )
        lines.extend(f"- `{path}`" for path in entry["code_paths"])
        lines.extend(["", "**Tests:**"])
        lines.extend(f"- `{path}`" for path in entry["tests"])
        lines.extend(["", "**Commands:**"])
        lines.extend(f"- `{command}`" for command in entry["commands"])
        lines.extend(["", "**Artifacts:**"])
        lines.extend(f"- `{path}`" for path in entry["artifacts"])
        lines.extend(
            [
                "",
                f"**Learning story:** {entry['learning_story']}",
                "",
                f"**Boundary:** {entry['boundary']}",
                "",
                "**Path checks:**",
            ]
        )
        for check in entry["path_checks"]:
            status = "present" if check["exists"] else "missing"
            lines.append(f"- `{check['path']}`: {status}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
