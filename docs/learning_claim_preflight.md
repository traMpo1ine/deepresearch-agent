# Claim Preflight 学习笔记

## 为什么做

Verifier 和 Red-Blue 是报告生成后的检查与修复机制。但有些问题可以在 Writer 输出前先做轻量处理：

- 重复 claim。
- 证据里已经出现 conflict cue。
- claim 使用 `always / never / guarantee / 完全 / 绝对` 这类过强表达。

这一步叫 Claim Preflight。它不是严格 NLI，也不替代 Verifier，只是写前防御。

## 怎么实现

`ClaimPreflight` 做三件事：

- duplicate claim detection：按规范化文本去重。
- conflicting evidence detection：扫描 evidence 中的冲突提示词。
- overclaim downgrade：把过强 claim 降为 `Evidence suggests that ...`，降低 confidence，并标记需要验证。

Writer 会把 preflight 结果写入：

```text
report.run_summary["claim_preflight"]
```

如果发现问题，也会把 limitations 写进报告。

## 为什么不用 LLM 直接改写

当前项目主线是离线可复现。LLM 改写可能让 claim 变得更顺，但也会引入随机性，并且很难稳定回归测试。Claim Preflight 是一个可解释 baseline，后续可以再和 LLM rewrite 做对照。

## 边界

Claim Preflight 只处理明显重复、明显冲突提示词和明显过强表达。真正的事实判断仍由 Verifier 和 Red-Blue 完成。
