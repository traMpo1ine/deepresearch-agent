# Red-Blue Convergence 学习笔记

## 为什么补这块

Red-Blue repair 如果只执行固定轮数，面试官会继续追问：什么时候停止？会不会反复修改同一句话？怎么知道修复在变好？

V3 增加 `RepairLoopTrace`，让每一轮 verify-repair 都能记录收敛和震荡信号。

## Trace 字段

- `round_index`
- `finding_count`
- `weak_claim_count`
- `repair_action_count`
- `claim_fingerprint_before`
- `claim_fingerprint_after`
- `converged`
- `oscillating`
- `stop_reason`

## 停止条件

- `CONVERGED`：没有 finding，或者弱支持 claim 没有继续恶化且没有严重 finding。
- `OSCILLATION`：claim fingerprint 重复，或同一 claim 被反复 MODIFY。
- `MAX_ROUNDS`：达到 `max_repair_rounds`。

## 学习命令

```powershell
uv run python scripts/inspect_redblue_convergence.py --case converged
uv run python scripts/inspect_redblue_convergence.py --case oscillation
uv run python scripts/inspect_redblue_convergence.py --case max_rounds --json
```

## 面试讲法

我把 Red-Blue 从“反思几轮”改成了可观测 repair loop：每轮记录 finding 数、弱 claim 数、动作数和 claim fingerprint。这样可以判断修复是否收敛，也可以发现反复修改同一 claim 的震荡情况。

## 边界

当前 fingerprint 是 deterministic heuristic，不是语义等价检测；后续可以用 LLM/NLI 判断“文本不同但语义相同”的震荡。
