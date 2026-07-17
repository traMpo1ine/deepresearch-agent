# 黄金真实数据案例

## 目标

这个案例不是再做一张好看的页面，而是用硬门禁证明以下链路真实发生：

```text
公开网页 -> 安全抓取 -> page/chunk Evidence -> 百炼 Embedding
        -> DeepSeek 引用写作 -> atomic verification -> 冻结报告
```

公开来源固定为：

1. NIST AI RMF Generative AI Profile；
2. OWASP LLM01:2025 Prompt Injection；
3. arXiv 论文 `Evaluation of Retrieval-Augmented Generation: A Survey`。

脚本：`scripts/run_golden_demo.py`

冻结结果：`reports/golden_demo/deepseek_v3/golden_summary.md`

## 运行

`.env` 需要配置百炼 Embedding 和 DeepSeek：

```dotenv
EMBEDDING_API_KEY=你的Key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4
DEEPSEEK_API_KEY=你的DeepSeek官方Key
```

执行：

```powershell
uv run python scripts/run_golden_demo.py --llm-backend deepseek
```

验收项包括：

- provider 必须是 `openai_compatible`；
- 模型必须与 `.env` 一致；
- 至少读取两个公开 host，冻结版本实际为三个；
- live-source lineage complete rate不低于0.9；
- 必须生成Evidence、Claim和VerificationTrace；
- 至少一条Claim必须真正引用HTTP来源；
- DeepSeek Writer不能回退到extractive模式。

任何一项失败，脚本以非零状态退出，不能把本地fallback包装成真实数据成功。

## 冻结结果

- 3个公开source hosts；
- 54条Evidence；
- DeepSeek Writer生成4条有效主张且`fallback=false`；
- 4/4具有verification trace并判定supported，其中3条分别引用NIST、OWASP、arXiv；
- source lineage complete rate为1.000；
- `text-embedding-v4`真实处理57个远程输入，run内其余78次由SQLite cache命中；
- DeepSeek处理1,399 tokens，冻结时估算成本为0.0002318568美元。

## 生成模式边界

冻结`deepseek_v3`是真实DeepSeek Writer单次受控运行证据，不代表普遍生成质量或生产SLA。Writer只允许使用给定evidence id；虚构citation id会被过滤，没有有效引用或JSON被截断时会回退到extractive，而黄金门禁会将这种情况判为失败。Claim按引用原文语言生成，标题与摘要可以使用问题语言，避免跨语言词面Verifier误删有依据的主张。
