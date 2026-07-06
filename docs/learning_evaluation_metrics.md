# Evaluation Metrics 学习笔记

## 为什么做

Agent 项目不能只展示一两个好看的输出。需要能回答：哪个模块带来了提升，提升体现在哪类任务上，失败样例是什么。

## 怎么实现

- ResearchBench 主集用于普通研究任务。
- Adversarial suite 用于 verifier / redblue 压力测试。
- `run_eval.py --suite researchbench|adversarial|all` 统一入口。
- `run_eval.py --config configs/default.toml` 读取默认 dataset、suite、experiment profiles 和 bootstrap samples。
- 保留 judge mean、Bootstrap 95% CI、Cohen's d。
- 增加 `atomic_support_rate`、`contradiction_detection_rate`、`repair_precision`、`repair_coverage`、`evidence_grounding_score`。
- 写入 metrics 前校验 payload：result 字段必须完整，summary 均值必须能由 result 明细重新计算。
- `EvalIntegrityReport` 记录 config snapshot、dataset summary、suite source counts、payload validation status 和每个实验的 artifact 路径。

## 失败案例和权衡

mock judge 是确定性的，适合回归测试，但不能代表真实用户偏好。当前指标更适合比较同一离线评测集上的配置差异，不能包装成线上模型效果。

`--suite all` 会生成 combined dataset，并在每条样例中写入 `suite_source`。这样后续做 failure analysis 时，可以区分普通 ResearchBench 失败和 adversarial 压力测试失败。

`EvalIntegrityReport` 的意义是让实验报告不只是一张分数表。后续写博客或复现实验时，可以直接说明：这次跑的是什么配置、多少题、题目来源、结果是否通过一致性校验，以及每个实验的运行产物在哪里。

## 怎么观察指标计算

完整 `run_eval.py` 会跑 35 题或更多样例，适合正式实验，但不适合刚开始理解指标。现在可以用固定 toy case 观察 baseline 和 redblue 的指标差异：

```powershell
uv run python scripts/inspect_eval_metrics.py --list
uv run python scripts/inspect_eval_metrics.py --case baseline_vs_redblue
uv run python scripts/inspect_eval_metrics.py --case baseline_vs_redblue --json
```

重点看：

- `judge_score_mean`：mock judge 的平均总分。
- `judge_score_bootstrap_95_ci`：对 judge score 均值做 bootstrap 得到的不确定区间。
- `cohens_d`：improved 相对 baseline 的效果量。
- `weak_support_rate`：弱支持 claim 的比例，越低越好。
- `atomic_support_rate`：atomic claim 被支持的比例，越高越好。
- `evidence_grounding_score`：atomic trace 中 term overlap 和 quote overlap 的平均支撑强度。

toy case 的作用是帮助理解指标，不代表真实系统效果。正式实验仍然使用：

```powershell
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue
```
