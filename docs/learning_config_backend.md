# Config and Backend Design 学习笔记

## 为什么做

长期项目里，参数如果散落在脚本和构造函数里，后面接真实 LLM、切实验配置、复现实验都会越来越痛。配置文件的目标是让默认行为稳定，让 CLI 只负责覆盖关键参数。

## 怎么实现

- `configs/default.toml` 保存 runtime、memory、llm、pipeline、evaluation 默认值。
- `deepresearch_agent.config.load_config()` 使用 Python 3.11 标准库 `tomllib`。
- CLI 参数优先级：命令行参数 > config > 代码默认值。
- 评测侧通过 `evaluation.dataset`、`evaluation.suite`、`evaluation.experiments`、`evaluation.bootstrap_samples` 控制默认运行参数。
- `experiments.profiles` 定义 baseline/memory/compression/verifier/redblue/full 的模块开关，避免实验配置散落在脚本里。
- mock backend 仍然是默认，真实 LLM 后端只在显式配置时启用。

## LLM Backend Factory

现在 LLM 后端有统一 factory：

```text
LLMBackendConfig -> create_llm_backend() -> Mock / OpenAI / DeepSeek / vLLM
```

观察命令：

```powershell
uv run python scripts/inspect_llm_backend.py --backend mock --smoke
uv run python scripts/inspect_llm_backend.py --backend deepseek --json
uv run python scripts/inspect_llm_backend.py --backend vllm --model local-model --vllm-base-url http://localhost:8000/v1 --json
```

设计原则：

- `mock` 默认离线可复现，可以执行 complete 和 embed smoke test。
- OpenAI / DeepSeek / vLLM 都走 OpenAI-compatible 风格接口。
- 真实后端默认 dry-run，只检查 base_url、model、env var，不访问网络。
- API key 从环境变量读取，不写进代码或配置文件。

`ResearchCoordinator` 现在会根据 `llm_backend / model / timeout / retries` 构造实际 backend 实例。当前 Agent 逻辑仍默认离线，后续可以逐步把 Planner 或 Writer 切到真实 backend。

## 失败案例和权衡

当前单题 research CLI 和批量 eval CLI 都接入了配置读取。真实 LLM backend 已经有 factory 和 dry-run 检查，但主评测仍保持 mock/offline 默认，避免 API 成本、网络波动和模型不确定性影响底层工程学习。
