# DeepResearch Agent 最终完成清单

这个清单用于判断项目是否已经达到“可复试讲、可简历写、可长期维护”的状态。

## A. 必须完成项

- [x] 使用 uv 管理环境和依赖。
- [x] README 提供快速开始、演示顺序、架构图、质量门。
- [x] PROJECT_DESIGN 与当前真实实现对齐。
- [x] Core schemas 覆盖 task、plan、evidence、claim、report、verification trace、repair action、evaluation result。
- [x] Agent 协议支持 `BaseAgent.run(input, context) -> AgentResult`，并保留各 Agent 专用方法。
- [x] Planner 支持 template baseline 和 heuristic adaptive planning。
- [x] DAGTaskGraph 支持依赖、拓扑批次、循环检测。
- [x] TaskStateMachine 支持任务生命周期和阻塞传播。
- [x] ResearchCoordinator 支持 asyncio + Semaphore 并发执行。
- [x] Searcher / Reader 支持离线 corpus、query expansion、quote extraction。
- [x] SQLiteMemoryStore 保存可审计运行轨迹。
- [x] NumpyVectorIndex 支持相似召回、save/load、损坏索引恢复。
- [x] TextRankCompressor 支持 quote preservation。
- [x] Writer 输出 Markdown 和 JSON。
- [x] Verifier 支持 atomic claims、best evidence、verification trace。
- [x] Red-Blue 支持 ADD / DELETE / MODIFY / VERIFY 修复动作。
- [x] Structured JSON fallback 支持 strict / fenced-substring / schema repair 三层解析。
- [x] Claim Preflight 支持写前去重、冲突提示和过强断言降级。
- [x] Evaluation 支持 ResearchBench、adversarial suite、Bootstrap CI、Cohen's d、failure cases。
- [x] LLM backend 支持 mock、OpenAI-compatible、DeepSeek、vLLM skeleton 和 smoke matrix。
- [x] Web Demo 支持默认 evidence pack 展示、mock/offline run、状态轮询和 DeepSeek provider smoke。
- [x] Showcase Pack 一条命令生成完整 trace。
- [x] BUILD_LOG 记录关键优化过程。
- [x] RESUME_NOTES 包含有边界的简历 bullet 和 3 分钟讲稿。
- [x] TRACEABILITY_MATRIX 和 inspect_resume_evidence 能把每条 bullet 追踪到代码、测试、命令和产物。

## B. 必须有的验证

- [x] `uv run ruff check src tests scripts`
- [x] `uv run pytest`
- [x] `uv run python -m compileall src scripts tests`
- [x] `uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？"`
- [x] `uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,memory,compression,verifier,redblue,full`
- [x] `uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue`
- [x] `uv run python scripts/inspect_llm_backend.py --backend mock --smoke`
- [x] `uv run python scripts/inspect_llm_backend.py --backend deepseek --json`
- [x] `uv run python scripts/inspect_llm_backend.py --backend vllm --model local-model --vllm-base-url http://localhost:8000/v1 --json`
- [x] `uv run python scripts/inspect_report_trace.py --report-json reports/showcase/final_check/report.json`
- [x] `uv run python scripts/inspect_resume_evidence.py --bullet verifier_redblue`
- [x] `uv run python scripts/inspect_structured_output.py --summary`
- [x] `uv run python scripts/run_redblue_eval.py`
- [x] `uv run python scripts/inspect_orchestration_stress.py --summary`
- [x] `uv run python scripts/run_backend_smoke_matrix.py`
- [x] `uv run python scripts/run_real_judge_smoke.py --backend mock --limit 5`
- [x] `uv run python scripts/run_final_experiments.py`
- [x] `uv run python scripts/check_project_completion.py`

## C. 当前正式产物

- Showcase Pack：`reports/showcase/final_check/index.md`
- Showcase LLM 后端记录：`reports/showcase/final_check/llm_backend.md`
- Web Demo：`scripts/run_demo_server.py`
- V3 ResearchBench run：`reports/experiments/20260702_162345_148429_researchbench_21c535de/summary.md`
- V3 Adversarial run：`reports/experiments/20260702_163315_852511_adversarial_f47f9b96/summary.md`
- Final evidence pack：`reports/final/final_sprint_check/index.md`
- 项目完成总账：`docs/PROJECT_COMPLETION_LOG.md`
- 最终项目报告：`docs/FINAL_PROJECT_REPORT.md`
- 实验记录：`docs/EXPERIMENTS.md`
- 学习路线：`docs/LEARNING_INDEX.md`
- 复试材料：`docs/RESUME_NOTES.md`
- 简历证据矩阵：`docs/TRACEABILITY_MATRIX.md`
- 完成验收脚本：`scripts/check_project_completion.py`

## D. 已知边界

- 当前主线是 offline/mock benchmark，不是线上系统。
- Mock LLM-as-Judge 只能比较项目内部配置，不能代表真实模型评分。
- Heuristic Verifier 不是严格 NLI，后续可以加 LLM/NLI 二级 verifier。
- Red-Blue 修复仍可能残留 prohibited claim cue，尤其是复杂过度概括或旧记忆场景。
- Benchmark 规模还小，CI 和 Cohen's d 用于实验叙事，不用于夸大泛化能力。

## E. 可选增强项

这些不是“项目完成”的必要条件。只有在主线稳定后再做。

- [x] 增加真实 LLM 单题 showcase，明确不混入 offline 指标。
- [ ] 增加 LLM/NLI verifier 作为第二层验证。
- [ ] 扩充 ResearchBench，让每类 answer_type 至少 7 题。
- [ ] 增加更多中文 corpus 和中文 query expansion。
- [ ] 用 FAISS/Chroma 替换 NumpyVectorIndex 做对照实验。
- [x] 做一个 notebook 或 Web UI 展示现有 Markdown/JSON 产物。
- [ ] 把 6 篇 blog 草稿润色成发布版。

## F. 项目完成判定

如果目标是“复试可讲 + 简历可写 + 后续能系统学习”，当前项目已经达到完成态。

如果目标是“真实可用 DeepResearch 产品”，还需要真实搜索、真实 LLM、多轮交互 UI、更大评测集和线上监控。这个不属于当前阶段。
