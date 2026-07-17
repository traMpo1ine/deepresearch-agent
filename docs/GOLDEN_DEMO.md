# 黄金真实数据案例

## 目标

这个案例不是再做一张好看的页面，而是用硬门禁证明以下链路真实发生：

```text
公开网页 -> 安全抓取 -> page/chunk Evidence -> 百炼 Embedding
        -> 确定性引用写作 -> atomic verification -> 冻结报告
```

公开来源固定为：

1. NIST AI RMF Generative AI Profile；
2. OWASP Top 10 for LLM / Prompt Injection；
3. arXiv 论文 `Evaluation of Retrieval-Augmented Generation: A Survey`。

脚本：`scripts/run_golden_demo.py`

冻结结果：`reports/golden_demo/v4/golden_summary.md`

## 运行

`.env` 只需要配置百炼 Embedding：

```dotenv
EMBEDDING_API_KEY=你的Key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4
```

执行：

```powershell
uv run python scripts/run_golden_demo.py
```

验收项包括：

- provider 必须是 `openai_compatible`；
- 模型必须与 `.env` 一致；
- 至少读取两个公开 host，冻结版本实际为三个；
- live-source lineage complete rate不低于0.9；
- 必须生成Evidence、Claim和VerificationTrace；
- 至少一条Claim必须真正引用HTTP来源；冻结版本为3/3。

任何一项失败，脚本以非零状态退出，不能把本地fallback包装成真实数据成功。

## 冻结结果

- 3个公开source hosts；
- 29条Evidence；
- 3条抽取式主张，分别引用NIST、OWASP、arXiv；
- 3/3具有verification trace并判定supported；
- source lineage complete rate为1.000；
- `text-embedding-v4`真实处理31个远程输入，run内其余104次由SQLite cache命中。

## 生成模式边界

当前`.env`没有DeepSeek Key，因此冻结v4采用`writer_mode=extractive`。它真实读取、选择、引用和验证公开证据，但不是LLM生成。

代码同时支持受约束LLM writer：

```powershell
uv run python scripts/run_golden_demo.py --llm-backend deepseek
```

该模式要求`DEEPSEEK_API_KEY`，并强制模型只使用给定evidence id；虚构citation id会被过滤，如果没有有效引用则回退到extractive并写入limitations。尚未真实执行前，简历不能写“DeepSeek完成黄金全链路生成”。
