# 实验记录

本文件用于记录每个里程碑的实验设置、指标和结果。

## Baseline

- Pipeline：mock Planner + mock Searcher + mock Reader + mock Writer。
- Dataset：`data/benchmarks/sample_researchbench.jsonl`。
- Metrics：事实准确率、幻觉率、引用覆盖率、LLM-as-Judge 分数。

## 当前实验脚本

运行：

```powershell
uv run python scripts/run_eval.py --dataset data/benchmarks/researchbench.jsonl --experiments baseline,memory,compression,verifier,redblue,full
uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue
uv run python scripts/run_eval.py --suite all --experiments baseline,verifier,redblue
uv run python scripts/run_eval.py --config configs/default.toml
```

当前支持的配置：

- `baseline`：无 memory recall、无 compression、无 verifier、无 redblue。
- `memory`：开启 memory recall。
- `compression`：开启 memory recall + TextRank compression。
- `verifier`：开启 memory recall + compression + verifier。
- `redblue` / `full`：开启完整 verifier + Red-Blue repair。

Planner 配置：

- `baseline` 使用 `planner_mode=template`，保持固定任务图。
- 其余配置默认使用 `planner_mode=heuristic`，根据问题类型生成不同 DAG。

关键指标：

- `hallucination_rate`：明确 unsupported / contradicted 的比例。
- `weak_support_rate`：需要更强证据、未知验证状态或弱支持的比例。
- `citation_coverage`：带 citation 的 claim 比例。
- `evidence_reuse_rate`：从历史记忆召回的 evidence 占比。
- `compression_ratio`：压缩后上下文字符数 / 原始 evidence 字符数。
- `repair_success_rate`：修复前后 weak claim 的下降比例。
- `atomic_support_rate`：atomic claim 中被证据支持的比例。
- `contradiction_detection_rate`：atomic claim 中被判为 contradicted 的比例。
- `repair_precision`：修复动作是否落在弱 claim、limitation 或 verify 目标上。
- `repair_coverage`：弱 claim 是否被 repair action 覆盖。
- `repair_convergence_rate`：Red-Blue repair loop 是否以收敛状态停止。
- `repair_oscillation_rate`：Red-Blue repair loop 是否检测到重复修改或 fingerprint 震荡。
- `avg_repair_rounds`：平均实际修复轮数。
- `evidence_grounding_score`：atomic trace 的 term overlap 与 quote overlap 平均值。
- `avg_task_latency`：Agent 事件平均耗时。
- `judge_score_bootstrap_95_ci`：judge score 的 bootstrap 95% CI。
- `cohens_d`：相对 baseline 配置的效果量。

## Adversarial Suite

新增 `data/benchmarks/adversarial_researchbench.jsonl`，专门测试 verifier / redblue 的薄弱点：

- no citation：无引用强断言。
- wrong citation：引用存在但不能支撑目标 claim。
- overclaim：把局部证据说成绝对结论。
- contradiction：与 evidence 中的限定或否定表达冲突。
- omission：重要 evidence 没有进入报告。
- vague claim：表达太虚，难以做 claim-evidence 对齐。
- stale memory：历史 evidence 被错误当作当前事实。
- over-compression：上下文压缩导致限制条件丢失。

最近一次本地检查：

- 命令：`uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue`
- 规模：10 题 adversarial researchbench。
- 观察：`redblue` 相比 `verifier` 将 hallucination_rate 从 0.067 降到 0.000，repair_precision 为 0.933，repair_coverage 为 1.000。
- 说明：这是 mock/offline 启发式实验，只能用于比较本项目内部配置，不能当作真实线上模型指标。

默认产物目录：

- `reports/experiments/<timestamp>/metrics.json`
- `reports/experiments/<timestamp>/summary.md`
- `reports/experiments/<timestamp>/failure_cases.md`

当前默认 run id 使用微秒级时间戳、suite 后缀和短 uuid，例如：

- `reports/experiments/20260627_205012_123456_researchbench_a1b2c3d4/`
- `reports/experiments/20260627_205012_654321_adversarial_e5f6a7b8/`

这样即使并行启动 ResearchBench 和 adversarial 评测，也不会因为同一秒时间戳而互相覆盖。显式传入 `--experiment-dir` 时仍以用户指定目录为准。

`summary.md` 可以直接复制到 README 或技术博客；`failure_cases.md` 用来做失败样例复盘。

## V3 Domain And Hotpot-style Subsets

ResearchBench 主集保持 35 题，但每题显式增加：

- `domain`
- `required_hops`
- `hotpot_style`

当前 domain 枚举：

```text
agent_orchestration
memory_retrieval
citation_verification
redblue_repair
evaluation
llm_backend
context_compression
rag_system
reliability
multi_hop
engineering_tradeoff
```

评测 summary 新增：

- `per_domain`
- `multi_hop_subset`
- `hotpot_style_subset`

命令：

```powershell
uv run python scripts/run_eval.py --config configs/default.toml --group-by domain
```

注意：这些仍然是 offline/mock benchmark 内部对比，不能写成线上效果。

## 配置化实验

`run_eval.py` 现在真正读取 `configs/default.toml`：

- `evaluation.dataset`：默认 ResearchBench 数据集。
- `evaluation.suite`：`researchbench`、`adversarial` 或 `all`。
- `evaluation.experiments`：默认实验组合，例如 `full`。
- `evaluation.bootstrap_samples`：Bootstrap CI 的采样次数。
- `experiments.profiles`：每个实验配置的 memory/compression/verifier/redblue 开关。

命令行参数会覆盖配置文件，例如：

```powershell
uv run python scripts/run_eval.py --config configs/default.toml --suite adversarial --experiments baseline,verifier,redblue
```

每个 experiment 仍会使用独立的 SQLite 和 vector index 文件，避免多配置评测互相污染。

`configs/default.toml` 是当前主配置。`experiments/*.yaml` 保留为轻量实验模板或历史兼容参考；如果二者冲突，以 `configs/default.toml` 和命令行参数为准。

## Payload Integrity

在写入 `metrics.json` 前，评测脚本会检查：

- 每个 result 是否包含 judge score、核心 rate、atomic metrics、repair metrics 和 failure analysis。
- summary 中的 rate 均值是否能由 results 重新计算得到。
- `judge_score_mean` 是否等于 result 明细中 overall judge score 的平均值。
- `--suite all` 生成的 combined dataset 会给每题写入 `suite_source`，用于后续区分来源。

`metrics.json` 还会写入 `integrity_report`：

- `config_snapshot`：本次运行使用的数据集、suite、实验配置、bootstrap samples 和默认 artifact 路径。
- `dataset_summary`：case 数量、answer type 分布、difficulty 分布、suite 来源分布和平均 required hops。
- `suite_source_counts`：ResearchBench 与 adversarial 样例数量。
- `experiment_artifacts`：每个实验的 SQLite、vector index 和 plan 目录。
- `payload_validation_status`：payload 校验是否通过。

后续每次优化需要记录：

- 改动内容
- 对照版本
- 数据集规模
- 指标均值
- Bootstrap 95% CI
- Cohen's d
- 失败样例分析

## 2026-07-02 V3 Formal Offline Benchmark

本轮用于 V3 机制补齐后的正式收束。和 2026-06-27 相比，本轮重点不是追求新数字，而是把新增机制纳入正式实验：

- 9 状态任务生命周期与 timeout/replan/fallback trace。
- Red-Blue repair loop convergence / oscillation / rounds 指标。
- 11 domain 标注、multi-hop subset、HotpotQA-style subset。
- payload integrity report 和 per-domain summary。

运行时出现过一次历史 `data/memory/vector_index_redblue.npz` 损坏 warning，系统按设计自动重建空 vector index 并继续实验。这说明“损坏运行产物不污染测试/实验”的工程保护是有效的。

### ResearchBench Main Suite

- Run id：`20260702_162345_148429_researchbench_21c535de`
- Dataset：`data/benchmarks/researchbench.jsonl`
- Suite：`researchbench`
- Cases：35
- Domains：11
- Multi-hop cases：13
- Hotpot-style cases：6
- Experiments：`baseline,memory,compression,verifier,redblue,full`
- 产物：
  - `reports/experiments/20260702_162345_148429_researchbench_21c535de/summary.md`
  - `reports/experiments/20260702_162345_148429_researchbench_21c535de/metrics.json`
  - `reports/experiments/20260702_162345_148429_researchbench_21c535de/failure_cases.md`

| experiment | judge | 95% CI | hallucination | weak support | atomic support | repair precision | repair coverage | convergence | oscillation | rounds | Cohen's d |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.774 | [0.759, 0.788] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 9.020 |
| memory | 0.779 | [0.766, 0.792] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.129 |
| compression | 0.779 | [0.765, 0.792] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.129 |
| verifier | 0.867 | [0.846, 0.887] | 0.105 | 0.667 | 0.471 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.760 |
| redblue | 0.878 | [0.858, 0.899] | 0.000 | 0.490 | 0.619 | 0.886 | 1.000 | 1.000 | 0.514 | 1.971 | 1.864 |
| full | 0.881 | [0.859, 0.903] | 0.000 | 0.490 | 0.619 | 0.886 | 1.000 | 1.000 | 0.514 | 1.971 | 1.933 |

Subset 观察：

- `full` multi-hop subset：n=13，judge=0.891，repair_precision=0.897。
- `full` Hotpot-style subset：n=6，judge=0.880，repair_precision=0.889。
- `redblue/full` repair action distribution：`add=18, delete=11, modify=48`。

解释：

- baseline/memory/compression 不启用 verifier，所以 weak_support_rate 为 1.000，表示 claim 没有经过强验证。
- verifier 会暴露 weak/unsupported claim，hallucination_rate 因而变得可见。
- redblue/full 在 verifier 基础上执行结构化 repair，使 hallucination_rate 降到 0.000，并给出 repair precision、coverage、convergence 和 oscillation 指标。
- oscillation_rate 不为 0 是一个真实边界：启发式 Blue Repair 在部分 claim 上会重复 MODIFY，因此 V3 把它显式记录，而不是隐藏掉。

### Adversarial Suite

- Run id：`20260702_163315_852511_adversarial_f47f9b96`
- Dataset：`data/benchmarks/adversarial_researchbench.jsonl`
- Suite：`adversarial`
- Cases：10
- Multi-hop cases：7
- Experiments：`baseline,verifier,redblue`
- 产物：
  - `reports/experiments/20260702_163315_852511_adversarial_f47f9b96/summary.md`
  - `reports/experiments/20260702_163315_852511_adversarial_f47f9b96/metrics.json`
  - `reports/experiments/20260702_163315_852511_adversarial_f47f9b96/failure_cases.md`

| experiment | judge | 95% CI | hallucination | weak support | atomic support | repair precision | repair coverage | convergence | oscillation | rounds | Cohen's d |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.791 | [0.772, 0.800] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 14.681 |
| verifier | 0.907 | [0.880, 0.933] | 0.100 | 0.567 | 0.643 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 3.134 |
| redblue | 0.913 | [0.890, 0.940] | 0.000 | 0.433 | 0.736 | 0.933 | 1.000 | 1.000 | 0.300 | 2.000 | 3.553 |

观察：

- adversarial suite 覆盖 no citation、wrong citation、overclaim、contradiction、omission、vague claim、stale memory、over-compression 等失败模式。
- redblue repair action distribution 为 `add=3, delete=2, modify=12`。
- redblue 将 verifier 的 hallucination_rate 从 0.100 降到 0.000，将 weak_support_rate 从 0.567 降到 0.433。
- failure_cases 仍能看到部分 prohibited claim cue 残留，说明 heuristic repair 还不能替代更强 NLI/LLM verifier。

## 2026-06-27 Final Offline Benchmark

本轮用于项目收尾，不把结果包装成线上能力，只作为 offline/mock benchmark 内部对比。

### ResearchBench Main Suite

- Run id：`20260627_163658`
- Dataset：`data/benchmarks/researchbench.jsonl`
- Suite：`researchbench`
- Cases：35
- Experiments：`baseline,memory,compression,verifier,redblue,full`
- 产物：
  - `reports/experiments/20260627_163658/summary.md`
  - `reports/experiments/20260627_163658/metrics.json`
  - `reports/experiments/20260627_163658/failure_cases.md`

| experiment | judge | 95% CI | hallucination | weak support | atomic support | repair precision | repair coverage | Cohen's d |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.774 | [0.759, 0.786] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 9.020 |
| memory | 0.779 | [0.764, 0.791] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.129 |
| compression | 0.779 | [0.766, 0.791] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.129 |
| verifier | 0.864 | [0.844, 0.885] | 0.105 | 0.667 | 0.471 | 0.000 | 0.000 | 1.727 |
| redblue | 0.881 | [0.859, 0.903] | 0.000 | 0.490 | 0.623 | 0.886 | 1.000 | 1.933 |
| full | 0.878 | [0.856, 0.902] | 0.000 | 0.490 | 0.619 | 0.886 | 1.000 | 1.864 |

观察：

- baseline/memory/compression 不启用 verifier，因此 weak_support_rate 为 1.000，表示 claims 没有经过强验证。
- verifier 暴露出 unsupported/weak claim，judge mean 从 0.774 提升到 0.864，但 hallucination_rate 变为 0.105，这是因为系统开始真实标记弱证据。
- redblue 在 verifier 基础上执行 repair actions，使 hallucination_rate 降到 0.000，weak_support_rate 降到 0.490。
- full 与 redblue 配置等价，因此指标接近；后续如果 full 增加真实 LLM 或更复杂记忆策略，再单独比较。

### Adversarial Suite

- Run id：`20260627_163936`
- Dataset：`data/benchmarks/adversarial_researchbench.jsonl`
- Suite：`adversarial`
- Cases：10
- Experiments：`baseline,verifier,redblue`
- 产物：
  - `reports/experiments/20260627_163936/summary.md`
  - `reports/experiments/20260627_163936/metrics.json`
  - `reports/experiments/20260627_163936/failure_cases.md`

| experiment | judge | 95% CI | hallucination | weak support | atomic support | repair precision | repair coverage | Cohen's d |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.791 | [0.772, 0.800] | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 14.681 |
| verifier | 0.907 | [0.880, 0.933] | 0.067 | 0.533 | 0.657 | 0.000 | 0.000 | 3.134 |
| redblue | 0.913 | [0.890, 0.940] | 0.000 | 0.433 | 0.736 | 0.933 | 1.000 | 3.553 |

观察：

- adversarial suite 专门覆盖 no citation、wrong citation、overclaim、contradiction、omission、vague claim、stale memory、over-compression 等失败模式。
- redblue repair action 分布为 `add=3, delete=2, modify=12`。
- redblue 将 verifier 的 hallucination_rate 从 0.067 降到 0.000，并将 weak_support_rate 从 0.533 降到 0.433。
- failure_cases 仍显示部分 prohibited claim cue 存在，说明启发式 Blue Repair 还不能完全替代更强的 NLI/LLM verifier，这是后续优化点。

### Result Boundary

- 所有结果来自本地 offline/mock benchmark。
- judge 是 mock LLM-as-Judge，用于比较本项目内部配置，不代表真实模型线上质量。
- 数据集规模较小，CI 和 Cohen's d 用于实验叙事，不用于夸大泛化能力。
- 简历中只能写“在自建离线评测集上可复现对比”，不能写“线上幻觉率下降”等无法验证表述。

## 2026-06-25 Comparison Grounding Check

本轮优化目标不是扩大功能，而是修复比较类问题的证据 grounding：

- Searcher 增加 query expansion，让中文“比较 / 向量数据库 / 优缺点”能命中英文离线语料。
- Corpus 增加 SQLite vs vector retrieval、vector database limitations、hybrid memory design 三篇比较类文档。
- Writer 的 comparison claims 改成更贴近 evidence 的可验证表述。
- Blue Repair 修复专名大小写问题，并去重重复 ADD limitation action。

检查命令：

```powershell
uv run ruff check src tests scripts
uv run pytest
uv run python -m compileall src scripts tests
uv run python scripts/run_research.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue
```

本地结果：

- 测试：`39 passed, 3 skipped`。
- 比较类 research：3 个 key claims 均为 `supported`。
- `redblue.judge_score_mean`: 0.881。
- `redblue.weak_support_rate`: 0.490。
- `redblue.atomic_support_rate`: 0.623。
- `technical_comparison.judge_score_mean`: 1.000。
- `technical_comparison.weak_support_rate`: 0.000。
- `technical_comparison.atomic_support_rate`: 1.000。
- `technical_comparison.evidence_grounding_score`: 0.684。

解释边界：

- 这是 offline/mock benchmark 内部对比结果。
- 当前 `technical_comparison` 类别样本数仍少，不能当作泛化结论。
- 这次结果主要说明：比较类链路从 Planner、Searcher、Writer 到 Verifier 已经形成一个可观察闭环。

## 2026-07-02 Final Sprint Evidence Pack

本轮目标是把对标简历效果的证据统一打包，入口为：

- `reports/final/final_sprint_check/index.md`

新增产物：

- `researchbench_summary.md`
- `adversarial_summary.md`
- `redblue_fixture_eval.md`
- `structured_output_eval.md`
- `backend_smoke_matrix.md`
- `real_judge_smoke.md`
- `completion_check.md`

核心结果：

| artifact | metric | value |
|---|---|---:|
| ResearchBench full | judge mean | 0.880 |
| ResearchBench full | repair_precision | 0.895 |
| ResearchBench full | repair_coverage | 1.000 |
| Adversarial redblue | judge mean | 0.920 |
| Adversarial redblue | repair_precision | 0.883 |
| Adversarial redblue | repair_coverage | 1.000 |
| Red-Blue fixtures | repair_success_before | 0.425 |
| Red-Blue fixtures | repair_success_after | 1.000 |
| Structured JSON fallback | parse_success_rate | 1.000 |

Structured JSON fallback 50 条 cases 的 Level 1/2/3 分布为 6/11/33。Red-Blue fixtures 扩展到 80 条，覆盖 no citation、wrong citation、overclaim、contradiction、omission、vague claim、stale memory、over-compression、JSON fallback overclaim、traceability 等 failure modes。

边界：

- final evidence pack 仍是 offline/mock 证据包。
- `real_judge_smoke.md` 默认使用 mock backend，只验证 LLM-as-Judge 接口链路。
- DeepSeek/OpenAI 真实 judge smoke 需要 API key 和显式 `--run-real`，不能和 offline/mock benchmark 指标混写。
