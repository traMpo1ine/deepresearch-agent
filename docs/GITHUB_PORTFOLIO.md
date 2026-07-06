# GitHub Portfolio Checklist

这份清单用于把 GitHub 仓库配置成面向 AI Agent / RAG / AI 应用实习投递的作品集入口。

## Repository Description

推荐仓库描述：

```text
Portfolio-ready DeepResearch Agent with multi-agent DAG orchestration, traceable RAG memory, verifier/red-blue repair, evaluation, DeepSeek verifier benchmark, and a local FastAPI web demo.
```

更短版本：

```text
Multi-agent DeepResearch/RAG system with traceable memory, verifier repair, evaluation, and FastAPI demo.
```

## Topics

推荐添加这些 GitHub topics：

```text
ai-agent
rag
deep-research
multi-agent
llm
fastapi
deepseek
evaluation
red-blue
sqlite
textrank
portfolio
```

## Website Field

如果暂时没有线上部署，Website 可以先留空。后续如果录了 Demo GIF 或部署到 Hugging Face Spaces / Railway / Render，再填演示地址。

## Visibility

投递前建议设为 Public。当前如果匿名访问 GitHub 返回 404，通常是仓库仍为 Private。

设置路径：

```text
GitHub repo -> Settings -> General -> Danger Zone -> Change repository visibility
```

## Pinned Repository Note

如果要 pin 到 GitHub Profile，建议 pin 文案重点看这三点：

- 能本地运行：FastAPI Web Demo + mock/offline pipeline。
- 有 Agent 工程链路：DAG orchestration + memory + verifier + repair。
- 有可复查证据：ResearchBench ablation + DeepSeek verifier benchmark + traceability matrix。
- 有可视化入口：README 顶部的 Demo GIF 能在 20-30 秒内展示默认 evidence pack、本地知识库 run、report 和 verification trace。

## First-Click Route

面试官或 HR 打开仓库后，推荐阅读路径：

1. README 顶部 30 秒速览和 Web Demo GIF。
2. `reports/final/pre_resume_evidence_pack/index.md` 看冻结指标。
3. `docs/TRACEABILITY_MATRIX.md` 看每条说法对应的代码、测试、命令和产物。
4. `docs/RESUME_NOTES.md` 看面试讲解版本。

## Do Not Upload

不要上传：

- `.env`
- API key
- `.venv/`
- `.uv-cache/`
- `data/memory/*.sqlite3`
- 临时 `reports/demo_runs/`
- 临时真实 API 原始输出，除非确认没有敏感内容
