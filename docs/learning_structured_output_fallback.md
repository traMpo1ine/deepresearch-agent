# Structured Output Fallback 学习笔记

## 为什么做

真实 LLM 输出结构化 JSON 时，经常会出现三类问题：

- 外面包了 Markdown 代码块。
- JSON 前后带解释性文本。
- 单引号、尾逗号、缺字段等轻微格式错误。

如果 Agent 系统直接 `json.loads()`，这些小问题会让整条 pipeline 失败；如果完全让 LLM 重新生成，又会引入网络、成本和随机性。因此项目先做一个离线、可测试的三层 fallback parser。

## 怎么实现

`StructuredOutputParser` 分三层：

1. Level 1：严格 `json.loads`。
2. Level 2：提取 fenced JSON 或首尾 `{...}` substring。
3. Level 3：修复常见格式问题，并用 schema defaults 补缺字段。

每次解析都会返回：

- `parse_ok`
- `parse_level`
- `parse_error`
- `parse_warnings`

OpenAI-compatible backend 的 `structured_complete()` 会把这些 metadata 放进返回对象的 `__parse_metadata__` 字段，后续可以统计解析成功率。

## 当前结果

固定样例：`data/examples/structured_output_cases.jsonl`

- Cases：30。
- Parse success：30。
- Parse success rate：1.000。
- 指标字段名：`parse_success_rate`。
- Level 1：4。
- Level 2：7。
- Level 3：19。

命令：

```powershell
uv run python scripts/inspect_structured_output.py --summary
uv run python scripts/inspect_structured_output.py --case combo_repair_001
```

## 边界

这个 parser 只能修复常见格式错误，不保证任意坏输出都能恢复。简历里可以写“三层 JSON fallback，并在 50 条 corrupted-output cases 上统计 parse success rate”，不能写“所有 JSON 输出都能修复”。
