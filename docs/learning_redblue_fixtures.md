# Red-Blue Fixtures 学习笔记

## 为什么做

Red-Blue 如果只在完整 pipeline 里看最终报告，很难判断修复是否真的正确。Fixtures 把坏报告样例固定下来，让修复动作可以被单元测试量化。

## 怎么实现

- `data/adversarial/redblue_fixtures.jsonl` 固定 80 条样例。
- 覆盖 no citation、wrong citation、overclaim、contradiction、omission、vague claim、stale memory、over-compression。
- severity 规则固定：4 表示事实矛盾或无证据强断言；3 表示错引用或引用不足；2 表示过度概括或遗漏；1 表示表达不清或需要限制。
- `tests/unit/test_redblue_fixtures.py` 要求至少 16 条动作正确，并且 ADD/DELETE/MODIFY/VERIFY 四类动作都被覆盖。

## 失败案例和权衡

当前 Blue Agent 仍然是规则修复。它适合验证 repair policy，但不会真正重写复杂段落。后续可以把 rule-based repair 和 LLM-based rewrite 分层：规则先决定动作类型，模型只负责生成候选文本。

## 怎么观察

除了 `data/adversarial/redblue_fixtures.jsonl` 这组偏测试的 fixtures，现在还有一组学习样例：

```powershell
uv run python scripts/inspect_redblue.py --list
uv run python scripts/inspect_redblue.py --case overclaim
uv run python scripts/inspect_redblue.py --case omission --json
```

学习样例在 `data/examples/redblue_cases.jsonl`，目标不是覆盖更多数据，而是把一条 Red-Blue 链路讲清楚：

```text
bad report -> Red finding -> Blue action -> before/after
```

## ADD / DELETE / MODIFY / VERIFY 怎么触发

- `DELETE`：无 citation 的强断言，或 verification status 是 `UNSUPPORTED / CONTRADICTED` 且 severity 高。
- `MODIFY`：claim 是 `PARTIAL`，或者表达过强但还有部分证据支持。
- `ADD`：存在 evidence 但报告没有体现，Red 触发 omission finding，Blue 添加 limitation。
- `VERIFY`：Red 收到一个已支持 claim 的 finding 时可以记录确认动作；如果 Red 没有发现问题，也可以没有 repair action。

## 一个 overclaim 例子

坏 claim：

```text
Red-Blue repair eliminates hallucination in all reports.
```

Evidence 只说：

```text
Red-Blue repair can reduce weak claims.
```

Red finding：

```text
category=factuality
severity=2
reason=Claim is only partially supported by cited evidence.
```

Blue action：

```text
MODIFY
Before: Red-Blue repair eliminates hallucination in all reports.
After: Evidence suggests that Red-Blue repair eliminates hallucination in all reports.
```

这个例子说明：部分支持的 claim 不一定要删除，先把强断言降级成谨慎表达。

## 本轮真实调试记录

做 `no_citation` 学习样例时，发现 Red 在没有 evidence 的报告上也会追加 omission finding，导致同一个 case 先 DELETE 又 ADD limitation。

修复方式：

```text
只有 report.evidence 非空时，才检查 omission。
```

这个改动让两类问题边界更清楚：

- 没有 citation / 没有 evidence：删除无法支撑的 claim。
- 有 evidence 但没有写进 report：添加 limitation 或谨慎补充。
