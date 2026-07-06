# Verifier 与 Red-Blue 幻觉修复

核心观点：可信 Agent 需要把“哪里不可信”显式化，再让修复动作可审计。

## Claim-Evidence Alignment

DeepResearch Agent 的报告不是一整段不可拆的自然语言，而是由 Claim、Evidence 和 Citation 组成。Verifier 的任务是检查每个 claim 是否被 citation 指向的 evidence 支持。当前离线版本先使用启发式方法：citation presence、term overlap、quote overlap、source trust 和 contradiction cues。真实 LLM verifier 可以以后接入，但启发式版本已经足够让验证链路可测试、可复现。

## Atomic Claims

长 claim 往往混合多个断言，例如“DAG 可以并发执行任务，并且 Semaphore 可以控制外部调用”。如果整体判断，很容易把部分支持误判成完全支持。因此 Verifier 会先拆成 atomic claims，再逐条输出 SUPPORTED、PARTIAL、UNSUPPORTED 或 CONTRADICTED。最终 Claim 状态由 atomic results 聚合得到：任一 atomic contradicted 则整体 contradicted；全部 supported 才算 supported；全部 unsupported 才算 unsupported；其他混合结果为 partial。

每条 atomic result 现在都会选择 best evidence，而不是把所有 citation 拼成一大段。选择分数由 term overlap、quote overlap 和 source trust 组成，并写入 `evidence_scores`。最终 trace 中保留 `evidence_id`、`best_quote`、`decision_reason` 和 contradiction cues，因此面试时可以直接展示某个 claim 为什么被判 partial 或 contradicted。

## Red Agent

Red Agent 从四个维度攻击报告：

- factuality：事实是否被证据支持。
- logic：推理是否过强或前后不一致。
- citation：引用是否缺失、错配或质量弱。
- omission：是否遗漏高价值证据。

每个 AttackFinding 都包含 target、category、severity、reason 和 suggested_check。这样攻击不是一句“再检查一下”，而是结构化的可执行问题列表。

## Blue Agent

Blue Agent 不做模糊重写，而是执行四类显式动作：

- ADD：从 unused evidence 添加 limitation 或 cautious claim。
- DELETE：删除 unsupported / contradicted claim。
- MODIFY：把强断言降级为 evidence suggests / may / in this corpus。
- VERIFY：对已支持 claim 记录确认动作。

每个 RepairAction 都保留 before/after 和 reason。这样修复过程可以被评测脚本、博客和面试复盘。

## Evaluation

修复效果不能只看最终文本是否顺眼。项目使用 hallucination_rate、weak_support_rate、atomic_support_rate、repair_precision、repair_coverage 和 repair action distribution 来比较修复前后变化。Red-Blue fixtures 里固定了 80 个坏报告样例，覆盖无引用、错引用、过度概括、矛盾 claim、遗漏证据、模糊表达、stale memory 和 over-compression，保证后续改动不会把修复能力悄悄弄坏。

新增 adversarial researchbench 后，可以用一条命令跑专门的对抗评测：

```powershell
uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue
```

最近一次本地 mock/offline 结果中，Red-Blue 将 adversarial suite 的 hallucination_rate 从 verifier 配置的 0.067 降到 0.000，同时 repair_precision 为 0.933、repair_coverage 为 1.000。这个数字不是线上能力宣称，而是用于说明同一离线评测集内的模块差异。
