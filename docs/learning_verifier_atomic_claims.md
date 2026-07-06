# Verifier Atomic Claims 学习笔记

## 为什么做

长 claim 经常混合多个事实。整体算 overlap 容易把“部分支持”误判成“完全支持”，也无法解释到底是哪一小句出了问题。Atomic claim verification 的目标是把验证粒度降到可审计、可测试、可展示。

## 怎么实现

- `VerifierAgent.split_atomic_claims()` 用英文连接词和中文/英文分号做第一版切分。
- 每条 atomic claim 单独选择 best evidence。
- best evidence 分数由 `term_overlap * 0.65 + quote_overlap * 0.25 + source_trust * 0.10` 组成。
- `AtomicVerificationResult` 保存 `evidence_id`、`best_quote`、`decision_reason` 和 `evidence_scores`。
- 聚合规则固定：任一 CONTRADICTED -> Claim CONTRADICTED；全部 SUPPORTED -> SUPPORTED；全部 UNSUPPORTED -> UNSUPPORTED；其他 -> PARTIAL。

## 怎么观察

现在有一组固定学习样例：

```powershell
uv run python scripts/inspect_verification.py --list
uv run python scripts/inspect_verification.py --case supported
uv run python scripts/inspect_verification.py --case mixed_atomic --json
```

样例文件在 `data/examples/verification_cases.jsonl`。它们不依赖 SQLite、Searcher 或真实 LLM，只构造最小的 `Claim + Evidence`，专门用来观察 Verifier 行为。

当前包含六类：

- `supported`：引用证据直接覆盖 claim。
- `partial`：证据有部分重叠，但关键术语缺失。
- `unsupported`：有 citation id，但 citation 不能支撑 claim。
- `contradicted`：claim 说绝对保证，evidence 给出限制或否定。
- `mixed_atomic`：一个 atomic claim supported，另一个 unsupported，整体 partial。
- `no_citation`：没有 citation id，直接 unsupported。

## 怎么读 VerificationTrace

先看顶层字段：

- `expected_status`：这个学习样例预期的状态。
- `actual_status`：当前 Verifier 实际判定。
- `citation_presence`：citation id 是否能对应到 evidence。
- `verification_reason`：给人读的总体理由。

再看每个 atomic result：

- `text`：被单独验证的小 claim。
- `status`：这个 atomic claim 的状态。
- `best_evidence`：当前认为最相关的 evidence id。
- `best_quote`：best evidence 中最关键的 quote。
- `term_overlap`：claim 重要词在 evidence 中命中的比例。
- `quote_overlap`：claim 重要词在 quote 中命中的比例。
- `missing_terms`：缺失词，通常最适合用来解释 partial / unsupported。
- `contradiction_cues`：触发矛盾判断的启发式线索。
- `decision_reason`：把 best evidence、overlap 和 contradiction cue 串起来的一句话。

读 trace 时不要先盯状态名，而是先问三件事：

```text
1. citation id 有没有连到 evidence？
2. best evidence 是不是我直觉上也会选的证据？
3. missing_terms 和 contradiction_cues 能不能解释这个状态？
```

如果这三件事说得通，Verifier 结果才算可解释。

## 一个典型 mixed atomic 例子

claim：

```text
Citation tracking binds claims to evidence and vector search guarantees perfect recall.
```

被切成：

```text
1. Citation tracking binds claims to evidence
2. vector search guarantees perfect recall
```

第一条被 evidence 支持，第二条没有证据支持，所以整体聚合成 `PARTIAL`。这就是 atomic verification 的价值：它不会把整句粗暴判成 supported，也不会直接丢掉已被支持的部分。

## 失败案例和权衡

当前切分仍然是启发式，对复杂从句、中文逗号并列、隐含因果还不够强。后续可以把切分独立成模块，并用 LLM verifier 或小型 NLI 模型替换纯 lexical 判断，但离线启发式版本更适合先练底层工程和测试。

另一个边界是：`term_overlap >= 0.35` 就可能判为 supported，这对学习和离线测试足够直观，但不是严格事实蕴含。后续如果要更真实，可以把 lexical overlap 和 NLI/LLM verifier 做成双层验证。
