# DeepResearch Agent Build Log

这个文件记录项目是如何一步步做出来的。重点不是包装结果，而是保留真实工程过程：为什么做、遇到什么问题、怎么解决、为什么不用别的方法、如何验证。

## 2026-06-25 Searcher Grounding

### Background

Heuristic Planner 已经能把“比较 SQLite 和向量数据库的优缺点”识别成 `comparison`，Writer 也能生成 comparison report。但报告里的 evidence 仍然会跑到 Cohen's d、简历材料等不相关语料上。

### Problem

Planner 只解决“怎么拆问题”，不保证 Searcher 找到正确证据。中文问题里的“比较 / 向量数据库 / 优缺点”很难命中本地英文语料里的 `vector retrieval`、`embedding similarity`、`hybrid memory design`。

### Decision

选择离线 query expansion，而不是直接接真实搜索或 LLM 改写：

- query expansion 可复现、可测试、适合学习信息检索基础。
- 真实搜索会引入网络和排序波动。
- LLM query rewrite 会掩盖底层检索逻辑，不利于先学工程机制。

### Implementation

- Searcher 增加中英文领域词扩展。
- Corpus 增加 SQLite vs vector retrieval、vector database limitations、hybrid memory design 三篇比较类语料。
- Writer 的 comparison claims 改得更贴近 evidence 原文。
- Blue Repair 修复 `SQLite` 被改成 `sQLite` 的专名大小写问题，并去重重复 ADD action。

### Validation

命令：

```powershell
uv run python scripts/run_research.py "比较 SQLite 和向量数据库的优缺点" --planner-mode heuristic
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue
```

结果：

- 比较类 report 的 3 个 key claims 均为 `supported`。
- `technical_comparison.judge_score_mean`: 1.000。
- `technical_comparison.weak_support_rate`: 0.000。
- `technical_comparison.atomic_support_rate`: 1.000。

### Interview Story

我发现 Planner 拆得对还不够，因为检索召回会决定证据地基。于是先不用 LLM，做了离线 query expansion 和比较类 corpus，让中文比较问题稳定召回 SQLite/vector/hybrid memory 证据，再让 Writer 的 claim 贴近 evidence，最终 Verifier 能把 claim 判成 supported。

## 2026-06-25 Verifier Observability

### Background

Verifier 已经能输出 atomic claim trace，但直接读完整 pipeline 的报告不利于学习，也不利于复现某个具体判断。

### Problem

如果只看最终 `SUPPORTED / PARTIAL / UNSUPPORTED / CONTRADICTED`，很难解释为什么这样判，也很难给面试官展示 best evidence、missing terms、decision reason。

### Decision

新增 fixed verification cases 和 inspect CLI，而不是改 Verifier 核心算法：

- 当前重点是可观察性，不是追求更复杂的 NLI。
- fixed cases 能把每种状态变成最小可复现样例。
- 不改核心逻辑可以避免把“学习工具”和“算法优化”混在一起。

### Implementation

- 新增 `data/examples/verification_cases.jsonl`。
- 新增 `scripts/inspect_verification.py`。
- 新增 `docs/generated/day03_verifier_trace.md`。
- 扩写 `docs/learning_verifier_atomic_claims.md`。

### Validation

命令：

```powershell
uv run python scripts/inspect_verification.py --case mixed_atomic --json
uv run pytest
```

结果：

- `mixed_atomic` 被拆成两个 atomic claims。
- 第一条 supported，第二条 unsupported，整体 partial。
- 全量测试通过：`44 passed, 3 skipped`。

### Interview Story

我把 Verifier 做成可观察模块，不只是输出状态，而是能展示每个 atomic claim 的 best evidence、term overlap、quote overlap 和 missing terms。这样可以解释“为什么一句长 claim 不能粗暴判 supported”，而要拆成更小的事实单元。

## 2026-06-26 Red-Blue Observability

### Background

Red-Blue 已经有 20 条 adversarial fixtures，但它们更偏测试 Blue action 是否正确，不够适合作为学习材料。下一步需要把“Red 发现问题 -> Blue 修复问题”的过程可视化。

### Problem

完整 pipeline 里 Red-Blue 修复发生在很多模块之后，不容易单独观察。实现学习样例时还暴露了一个规则问题：当报告里没有任何 evidence 时，Red 仍然会追加 omission finding，导致 no-citation case 同时出现 DELETE 和 ADD。

### Decision

新增 Red-Blue learning cases 和 inspect CLI，并修正 omission 规则：

- 学习样例覆盖 no citation、wrong citation、overclaim、contradiction、omission、vague claim、supported clean。
- `inspect_redblue.py` 输出 finding、repair action、before/after。
- omission 只在 report 确实存在 evidence 时检查，避免无 evidence 报告被误判为遗漏证据。

### Implementation

- 新增 `data/examples/redblue_cases.jsonl`。
- 新增 Red-Blue case loader 和 trace renderer。
- 新增 `scripts/inspect_redblue.py`。
- 新增 `tests/unit/test_redblue_cases.py`。
- 更新 Red omission 规则：只有 `report.evidence` 非空时才检查 omission。

### Validation

命令：

```powershell
uv run python scripts/inspect_redblue.py --case no_citation
uv run python scripts/inspect_redblue.py --case omission --json
uv run pytest tests/unit/test_redblue_cases.py tests/unit/test_redblue.py tests/unit/test_redblue_fixtures.py
```

结果：

- no citation 只触发 DELETE。
- omission 触发 ADD limitation。
- Red-Blue 局部测试：`11 passed`。

### Interview Story

我把 Red-Blue 从“完整 pipeline 里看最终结果”拆成固定学习样例。Red 负责输出 AttackFinding，包括 category、severity、reason；Blue 根据 finding 执行 DELETE、MODIFY、ADD 或无修复。过程中发现 omission 规则会在无 evidence 时误报，于是把规则收紧成只有存在 evidence 才检查遗漏。

## 2026-06-26 Compression Observability

### Background

项目已经实现 TextRank 上下文压缩，核心目标是复现简历里的“L1 Embedding 粗过滤 -> L2 TextRank 细筛选 -> L3 原文保留”。但之前只能从完整 pipeline 的最终 report 里间接看到压缩效果，不适合学习和面试讲解。

### Problem

上下文压缩最怕的问题不是压得不够短，而是把 citation quote 压没了。quote 一旦丢失，Writer 后面的 claim-citation 绑定和 Verifier 的 quote overlap 都会变弱。

### Decision

新增 compression learning cases 和 inspect CLI，而不是直接接 LLM summarizer：

- LLM summarizer 可能改写引用原文，不利于保持证据链。
- 固定样例能明确展示 original chars、compressed chars、compression ratio 和 preserved quotes。
- 当前重点是可观察、可复现、可测试。

### Implementation

- 新增 `data/examples/compression_cases.jsonl`。
- 新增 compression case loader 和 trace renderer。
- 新增 `scripts/inspect_compression.py`。
- 新增 `tests/unit/test_compression_cases.py`。
- 新增 `docs/generated/day05_compression_trace.md`。

### Validation

命令：

```powershell
uv run python scripts/inspect_compression.py --case quote_preservation
uv run python scripts/inspect_compression.py --case multi_quote_preservation --json
uv run pytest tests/unit/test_compression.py tests/unit/test_compression_cases.py
```

结果：

- `quote_preservation` 在 `max_sentences=1` 时仍保留 1/1 quote。
- `multi_quote_preservation` 在 `max_sentences=1` 时保留 2/2 quotes。
- 压缩局部测试：`5 passed`。

### Interview Story

我把上下文压缩分成 L1/L2/L3 三层：先用 embedding 做候选粗筛，再用 TextRank 选高 salience 句子，最后强制保留 citation quote。这样不是单纯追求短，而是在压缩时保护后续 Verifier 需要的证据链。

## 2026-06-26 Memory Retrieval Observability

### Background

项目已经有 SQLiteMemoryStore 和 NumpyVectorIndex，但之前只能分别测试 SQLite roundtrip 和 vector search。图片中的简历强调“跨 Agent 共享记忆（SQLite + numpy 向量索引）”，所以需要展示二者如何协同。

### Problem

如果只说“用了 SQLite 和向量索引”，面试时容易变成堆技术名词。真正要讲清楚的是：vector index 只返回相似 evidence id，SQLite 才保存完整 source/chunk/quote，可审计链路不能丢。

### Decision

新增 memory learning cases 和 inspect CLI：

- 使用临时 SQLite 和临时 numpy index，不污染 `data/memory` 运行产物。
- 固定样例展示 vector recall -> SQLite get_evidence 的完整路径。
- 不引入 FAISS/Chroma 等外部向量库，先用 numpy 学清楚 cosine similarity 和 id 回表机制。

### Implementation

- 新增 `data/examples/memory_cases.jsonl`。
- 新增 memory case loader 和 trace renderer。
- 新增 `scripts/inspect_memory_trace.py`。
- 新增 `tests/unit/test_memory_cases.py`。
- 新增 `docs/generated/day06_memory_trace.md`。
- 处理 Windows 临时 SQLite 文件清理锁问题：TemporaryDirectory 使用 `ignore_cleanup_errors=True`。

### Validation

命令：

```powershell
uv run python scripts/inspect_memory_trace.py --case sqlite_vector_recall
uv run python scripts/inspect_memory_trace.py --case hybrid_memory_recall --json
uv run pytest tests/unit/test_memory_cases.py tests/unit/test_sqlite_memory.py tests/unit/test_vector_index.py
```

结果：

- `sqlite_vector_recall` 的 top vector hit 为 `ev_memory_citation`，并能回表拿到 quote/source/chunk。
- `hybrid_memory_recall` 的 top vector hit 为 `ev_hybrid_vector`。
- Memory 局部测试：`6 passed`。

### Interview Story

我没有直接上向量数据库，而是先用 numpy 实现轻量向量索引。向量索引用来召回相似 evidence id，SQLite 保存完整原文、chunk、quote 和 metadata。这样既能做语义召回，又能保留可审计的 claim-citation-source 链路。

## 2026-06-26 Evaluation Metrics Observability

### Background

项目已经支持 ResearchBench-style 批量评测、mock LLM-as-Judge、Bootstrap CI、Cohen's d 和 per-category summary。但完整 `run_eval.py` 输出很大，不适合初学阶段理解每个指标。

### Problem

如果只看一张最终 metrics 表，很难讲清楚：均值从哪里来，CI 表示什么，Cohen's d 为什么要和 baseline 比，weak_support_rate 和 atomic_support_rate 各自说明什么。

### Decision

新增 evaluation toy case 和 inspect CLI：

- 用 3 条 baseline + 3 条 improved 固定结果展示指标变化。
- 复用现有 `summarize_results`、`bootstrap_ci`、`cohens_d`，不重复造指标逻辑。
- 明确 toy case 只用于学习，不当作正式实验结果。

### Implementation

- 新增 `data/examples/evaluation_cases.jsonl`。
- 新增 evaluation case loader 和 trace renderer。
- 新增 `scripts/inspect_eval_metrics.py`。
- 新增 `tests/unit/test_evaluation_cases.py`。
- 新增 `docs/generated/day07_eval_metrics_trace.md`。

### Validation

命令：

```powershell
uv run python scripts/inspect_eval_metrics.py --case baseline_vs_redblue
uv run python scripts/inspect_eval_metrics.py --case baseline_vs_redblue --json
uv run pytest tests/unit/test_evaluation_cases.py tests/unit/test_evaluation_runner.py
```

结果：

- improved judge mean 高于 baseline。
- weak_support_rate delta 为负。
- atomic_support_rate delta 为正。
- Cohen's d 为正。
- Evaluation 局部测试：`10 passed`。

### Interview Story

我没有只展示几个好看的报告，而是做了离线评测体系。为了能讲清楚指标，我先构造 toy case 展示 baseline 和 redblue 的均值、bootstrap CI、Cohen's d 和 weak support 变化；正式实验再用 `run_eval.py` 跑 ResearchBench。

## 2026-06-27 LLM Backend Factory

### Background

项目已有 Mock、OpenAI-compatible、DeepSeek、vLLM 后端类，但 Coordinator 之前只是记录 `llm_backend` 字符串，没有统一 factory，也缺少一个不访问网络的配置检查入口。

### Problem

如果简历里写“支持多 LLM 后端”，面试官可能会追问：怎么切？API key 放哪？无 key 时测试会不会失败？真实模型结果和离线结果能不能混写？这些都需要工程边界。

### Decision

新增 LLM backend factory 和 inspect CLI：

- 默认 mock backend 离线可运行。
- OpenAI / DeepSeek / vLLM 走 OpenAI-compatible adapter。
- 真实后端默认 dry-run，只检查 base_url、model、env var，不访问网络。
- 只有显式 `--smoke` 时才发起真实 chat completion 调用。

### Implementation

- 新增 `LLMBackendConfig`、`create_llm_backend()`、`backend_status()`。
- `ResearchCoordinator` 根据配置构造实际 backend 实例。
- 新增 `scripts/inspect_llm_backend.py`。
- 新增 `tests/unit/test_llm_factory.py`。
- 新增 `docs/generated/day08_llm_backend_trace.md`。

### Validation

命令：

```powershell
uv run python scripts/inspect_llm_backend.py --backend mock --smoke
uv run python scripts/inspect_llm_backend.py --backend deepseek --json
uv run python scripts/inspect_llm_backend.py --backend vllm --model local-model --vllm-base-url http://localhost:8000/v1 --json
uv run pytest tests/unit/test_llm_factory.py tests/integration/test_llm_backends.py
```

结果：

- mock backend complete/embed smoke test 通过。
- DeepSeek/vLLM dry-run 能显示 env var 未配置但不访问网络。
- LLM factory 局部测试：`4 passed, 3 skipped`。

### Interview Story

我把模型调用和 Agent 逻辑解耦成统一 `LLMBackend` 接口。默认 mock 保证离线可复现；OpenAI、DeepSeek、vLLM 通过 OpenAI-compatible adapter 接入；API key 只从环境变量读取。这样本地测试不依赖网络，真实模型只是可选增强。

## 2026-06-27 Showcase Pack

### Background

项目已经有 Planner、DAG、Memory、Compression、Verifier、Red-Blue、Evaluation 等模块，也有很多 `inspect_*` 学习脚本。但这些入口比较分散，新读者很难一眼看出“一个问题如何走完整条 DeepResearch 链路”。

### Problem

如果只给单独脚本，项目容易看起来像功能堆叠：Planner 能跑、Verifier 能跑、Eval 能跑，但缺少一个把它们串起来的作品级入口。对学习来说，也缺少一个固定产物目录，方便从 `index.md` 开始逐个追踪。

### Decision

新增 showcase pack，而不是做复杂 UI：

- 保持离线可复现，不依赖真实 LLM 或网络。
- 每次运行使用独立 memory/vector/plan 路径，避免污染长期实验数据。
- 一条命令生成 Markdown/JSON 产物，方便学习、复盘和后续写博客。
- 产物覆盖完整链路，而不是只输出最终 report。

### Implementation

- 新增 `src/deepresearch_agent/showcase.py`，封装展示包生成逻辑。
- 新增 `scripts/run_showcase.py`，提供命令行入口。
- 输出 `plan.md`、`report.md`、`report.json`、`run_summary.json`。
- 输出 `memory_trace.md`、`compression_trace.md`、`verifier_trace.md`、`redblue_trace.md`、`eval_summary.md`。
- 输出 `interview_notes.md` 和 `index.md`，作为学习入口。
- 新增集成测试，确保完整产物集合不会退化。

### Validation

命令：

```powershell
uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？"
uv run pytest tests/integration/test_showcase.py
```

验收点：

- `reports/showcase/<timestamp>/index.md` 是总入口。
- `report.json` 可被程序读取。
- `memory_trace.md` 能从 citation 追到 SQLite evidence。
- `verifier_trace.md` 能看到 atomic claim 的 best evidence 和 decision reason。
- `redblue_trace.md` 能看到 repair action。

### Interview Story

我发现模块越来越多以后，最重要的不是继续堆新功能，而是做一个能展示完整工程链路的入口。所以我加了 showcase pack：一条命令从问题出发，生成规划 DAG、研究报告、记忆追踪、压缩追踪、验证追踪、Red-Blue 修复记录和评测摘要。这样项目不只是“有很多模块”，而是能证明每个模块都接在同一条可复现流水线上。

## 2026-06-27 Final Offline Evaluation

### Background

Showcase Pack 证明了单题链路完整，但简历和复试还需要一份正式实验记录，说明不同 pipeline 配置在同一离线 benchmark 上有什么差异。

### Problem

如果只展示一个好看的报告，面试官很难判断系统是否稳定。另一方面，真实 LLM 或线上数据会引入 API 成本、网络波动和不可复现输出，不适合作为当前阶段的主实验。

### Decision

使用当前 offline/mock 体系跑两轮正式实验：

- ResearchBench 主集：35 题，比较 baseline、memory、compression、verifier、redblue、full。
- Adversarial suite：10 题，比较 baseline、verifier、redblue。

所有结果只用于项目内部配置对比，不写成线上指标。

### Implementation

- 使用 `run_eval.py` 生成 `summary.md`、`metrics.json` 和 `failure_cases.md`。
- 使用 config-driven experiment profiles，保证每个实验配置的 memory/vector path 隔离。
- 将结果整理进 `docs/EXPERIMENTS.md`，并明确 result boundary。

### Validation

命令：

```powershell
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,memory,compression,verifier,redblue,full
uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue
```

结果：

- ResearchBench run：`20260627_163658`，35 题。
- Adversarial run：`20260627_163936`，10 题。
- ResearchBench 上 redblue judge mean 为 0.881，hallucination_rate 为 0.000，repair_precision 为 0.886，repair_coverage 为 1.000。
- Adversarial suite 上 redblue judge mean 为 0.913，hallucination_rate 为 0.000，repair_precision 为 0.933，repair_coverage 为 1.000。

### Interview Story

我没有把几个样例报告当成果，而是用同一个离线评测集比较 baseline、verifier、redblue 等配置。这个实验能说明 Verifier 会暴露弱支持 claim，Red-Blue 会进一步执行结构化修复动作。但我也明确限制了结论边界：这是 mock/offline benchmark，不是线上能力宣称。

## 2026-06-27 Real LLM Smoke Boundary

### Background

项目代码已经有 Mock、OpenAI-compatible、DeepSeek 和 vLLM 后端。如果说“支持多 LLM 后端”，就必须说明默认行为、API key 管理和真实调用边界。

### Problem

真实 LLM 调用会引入网络、费用和随机性。如果把它放进默认测试或主评测，就会破坏离线可复现；但完全不提供入口，又无法证明后端适配是可用设计。

### Decision

真实 LLM 只做 smoke，不进入主线实验：

- 默认 backend 永远是 mock。
- 无 key 时 dry-run 只检查配置，不访问网络。
- 有 key 时用户显式加 `--smoke` 才发起一次 completion。
- mock/offline 指标和真实 LLM 输出不能混写。

### Implementation

- `inspect_llm_backend.py` 作为配置检查入口。
- API key 只从 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY`、`VLLM_API_KEY` 读取。
- vLLM 默认 base url 为 `http://localhost:8000/v1`。
- README 增加真实后端边界说明。

### Validation

命令：

```powershell
uv run python scripts/inspect_llm_backend.py --backend mock --smoke
uv run python scripts/inspect_llm_backend.py --backend deepseek --json
uv run python scripts/inspect_llm_backend.py --backend vllm --model local-model --vllm-base-url http://localhost:8000/v1 --json
```

### Interview Story

我把真实 LLM 后端设计成可选增强，而不是默认依赖。这样项目核心能力可以在无网络环境稳定复现；需要展示真实模型时，再通过统一 backend adapter 做 smoke test。这个边界能避免把不可复现的模型输出混进离线实验结果。

## 2026-06-27 Completion Gate

### Background

项目进入收尾后，源码、文档、展示包和实验产物都已经很多。只靠口头说“项目完成了”不够稳，也不方便以后复习。

### Problem

README、PROJECT_DESIGN、实验报告和 showcase 可能逐渐不同步。如果没有一个验收入口，后续改动很容易漏掉关键产物，比如忘记保留 `metrics.json`、忘记更新最终项目报告，或者 README 里的边界说明被删掉。

### Decision

新增一个轻量 completion gate，而不是再跑一遍长实验：

- 检查关键源码、脚本、数据集、学习文档是否存在。
- 检查 showcase 和正式实验产物是否存在。
- 检查 README、PROJECT_DESIGN、PROJECT_COMPLETION_LOG 是否包含关键边界表达。
- 支持 Markdown/JSON 输出，方便人工看或脚本消费。

### Implementation

- 新增 `scripts/check_project_completion.py`。
- 新增 `tests/unit/test_completion_check.py`。
- README 和最终完成清单加入验收命令。

### Validation

命令：

```powershell
uv run python scripts/check_project_completion.py
uv run pytest tests/unit/test_completion_check.py
uv run ruff check src tests scripts
```

结果：

- completion check：`passed`。
- path checks：53，missing paths：0。
- text checks：12，missing text checks：0。
- 单测：`2 passed`。

### Interview Story

项目越接近完成，越需要工程化验收。我加了 completion gate，把“源码是否齐全、实验产物是否存在、文档是否讲清边界”变成一条可运行命令。这样项目不是靠主观判断完成，而是有一套可复现的完成态检查。

## 2026-06-27 Final Project Report

### Background

README、PROJECT_DESIGN、EXPERIMENTS 分别解决不同问题，但它们比较分散。项目完成后，需要一份可以从头读到尾的正式结项报告。

### Problem

如果未来学习时只看 README，会知道怎么运行，但不一定能理解每个模块为什么这样设计；如果只看 BUILD_LOG，会看到过程，但不够像最终交付文档；如果只看 EXPERIMENTS，又缺少架构与完整结论。

### Decision

新增最终项目报告：

- 汇总项目摘要、系统架构、模块完成情况。
- 汇总 ResearchBench 和 adversarial 正式实验结果。
- 明确结果边界，避免把 offline/mock 指标包装成线上效果。
- 给出复试讲解摘要和后续增强方向。

### Implementation

- 新增 `docs/FINAL_PROJECT_REPORT.md`。
- README 和 LEARNING_INDEX 增加入口。
- Completion gate 增加最终报告存在性和关键文本检查。

### Validation

命令：

```powershell
uv run python scripts/check_project_completion.py
uv run pytest tests/unit/test_completion_check.py
```

### Interview Story

我把最终成果整理成一份项目报告，而不是让信息散在 README、实验记录和简历材料里。这样可以从工程交付角度讲清楚：系统架构是什么、每个模块解决什么问题、实验结果如何、哪些结论有边界。

## 2026-06-27 Showcase LLM Backend Integration

### Background

`run_research.py` 已经支持 `--llm-backend` 和 `--model`，`inspect_llm_backend.py` 也能检查 OpenAI / DeepSeek / vLLM 配置。但 showcase 是项目最重要的演示入口，之前只能默认 mock，不能展示后端配置。

### Problem

如果 README 说项目支持多 LLM 后端，但 showcase pack 里没有 backend trace，复试时容易被追问：真实后端到底有没有接到主链路？vLLM base url 能不能从 CLI 传？run summary 里能不能追踪 backend/model？

### Decision

补齐主链路的 backend 配置记录，而不是让它只停留在 inspect 脚本：

- `ResearchCoordinator` 记录 `llm_status` 和 `llm_vllm_base_url`。
- `run_research.py` 支持 `--vllm-base-url`。
- `run_showcase.py` 支持 `--llm-backend`、`--model`、`--timeout-seconds`、`--max-retries`、`--vllm-base-url`。
- showcase pack 增加 `llm_backend.md`。

### Implementation

- Coordinator 使用同一个 `LLMBackendConfig` 创建后端和生成 status。
- Showcase 生成 `llm_backend.md`，展示 backend、model、base url、env var、offline_safe 和 run summary 后端字段。
- Completion gate 将 `reports/showcase/final_check/llm_backend.md` 纳入验收。

### Validation

命令：

```powershell
uv run pytest tests/unit/test_llm_factory.py tests/integration/test_showcase.py
uv run python scripts/run_showcase.py "为什么 DeepResearch Agent 需要引用验证？" --output-dir reports/showcase/final_check --llm-backend mock --model mock-researcher-v0
uv run python scripts/check_project_completion.py
```

结果：

- LLM/showcase 局部测试：`6 passed`。
- completion check：`passed`。
- showcase artifacts：10/10 present。

### Interview Story

我发现多 LLM 后端不能只停留在一个 inspect 脚本里，所以把 backend config 接进了主运行链路和 showcase。现在一次 showcase 不只生成报告和验证 trace，还会生成 `llm_backend.md`，说明当前用的 backend、model、base url、env 配置和 offline safety。这样可以清楚地区分离线 mock 实验和真实 LLM smoke。

## 2026-06-27 SQLite Migration Hardening

### Background

SQLite Memory 是项目的长期运行产物。随着 Verifier、Red-Blue、LLM backend trace 逐步增加，schema 会继续变化。旧数据库如果缺字段，不应该直接导致项目崩掉。

### Problem

之前已有 `schema_migrations` 表和 `_ensure_column()`，但缺少可查询的 schema version，也没有测试证明旧版 `verification_traces` 表能自动补 `atomic_results`。这会让“支持长期维护”停留在口头层面。

### Decision

做轻量 migration，而不是引入复杂迁移框架：

- 使用 `PRAGMA user_version` 记录当前 schema version。
- 使用 `schema_migrations` 记录应用过的版本和说明。
- 保留 `_ensure_column()` 处理当前最重要的旧库补列。
- 增加旧库升级测试。

### Implementation

- 新增 `SCHEMA_VERSION = 2` 和 migration 描述表。
- 新增 `SQLiteMemoryStore.schema_version()`。
- 新增 `SQLiteMemoryStore.list_schema_migrations()`。
- 测试手工构造旧版 `verification_traces` 表，验证初始化 store 后自动补 `atomic_results`。

### Validation

命令：

```powershell
uv run pytest tests/unit/test_sqlite_memory.py
uv run ruff check src tests scripts
```

结果：

- SQLite memory 局部测试：`3 passed`。
- ruff passed。

### Interview Story

我没有把 SQLite 当成一次性运行缓存，而是把它当作长期 Agent memory。随着 verification trace 字段增加，旧库可能缺列，所以我加了轻量 migration：用 `PRAGMA user_version` 标记版本，用 `schema_migrations` 留记录，用 `_ensure_column()` 做安全补列。这样以后 schema 演进不会轻易破坏历史实验。

## 2026-06-27 Memory Inspection CLI

### Background

SQLite migration 和共享记忆已经实现，但普通用户只能通过测试或源码确认 schema version 和 migration 记录。`inspect_memory.py` 之前只会列 evidence，不足以调试真实运行产物。

### Problem

复试或学习时，如果要证明 SQLite 是共享记忆层，需要能直接展示：当前数据库版本是多少、有哪些 migration、各表有多少记录、最近有哪些 run，以及 evidence 能否被列出。

### Decision

增强现有 `inspect_memory.py`，而不是再新增一个脚本：

- 保留默认列 evidence 的兼容行为。
- 增加 `--schema` 查看 schema version、migrations 和 table counts。
- 增加 `--runs` 查看最近运行。
- 增加 `--json` 支持机器可读输出。

### Implementation

- `SQLiteMemoryStore` 新增 `list_runs()` 和 `database_summary()`。
- `inspect_memory.py` 输出 Markdown 或 JSON。
- Completion gate 检查 `inspect_memory.py` 包含 schema/runs inspection 能力。

### Validation

命令：

```powershell
uv run python scripts/inspect_memory.py --memory-path reports/showcase/final_check/memory.sqlite3 --schema --runs --limit 3
uv run pytest tests/unit/test_sqlite_memory.py tests/unit/test_inspect_memory_script.py
```

结果：

- 输出 schema version：2。
- 输出 migrations：v1、v2。
- 输出 table counts、recent runs 和 evidence。
- 局部测试：`6 passed`。

### Interview Story

我把 SQLite memory 做成可检查的运行产物，而不是只在代码里说“有共享记忆”。现在可以一条命令看到 schema version、migration 历史、各表记录数、最近 run 和 evidence，这能证明 Agent trace 和 citation evidence 确实被持久化保存。

## 2026-06-27 Report Trace Inspection

### Background

Showcase Pack 已经能生成 `report.json`，Verifier 也会写入 `verification_trace`。但如果只拿到一份 report JSON，用户还需要手动翻 JSON 才能理解 claim、citation、evidence、atomic verification 和 repair action 的关系。

### Problem

“引用追踪”和“幻觉检测”不能只存在于数据结构里。复试或学习时，需要一条命令直接展示：每个 claim 引用了哪些 evidence、引用是否能在报告 evidence 中找到、Verifier 如何判定、Red-Blue 是否修复过。

### Decision

新增 report trace inspection CLI：

- 输入 `report.json`。
- 输出 claim -> citation -> evidence -> verification trace -> atomic results -> repair actions。
- 支持 `--claim-id` 只看单个 claim。
- 支持 `--json` 输出机器可读 payload。

### Implementation

- 新增 `scripts/inspect_report_trace.py`。
- 新增 `tests/unit/test_inspect_report_trace.py`。
- README、LEARNING_INDEX、FINAL_COMPLETION_CHECKLIST 增加入口。
- Completion gate 检查该脚本存在并包含关键 trace 输出能力。

### Validation

命令：

```powershell
uv run python scripts/inspect_report_trace.py --report-json reports/showcase/final_check/report.json
uv run pytest tests/unit/test_inspect_report_trace.py
```

结果：

- 能输出 report 的 citation coverage、verification status counts。
- 能逐 claim 展示 citation evidence quote。
- 能展示 atomic results 和 repair actions。
- 局部测试：`3 passed`。

### Interview Story

我把“引用追踪”做成了可操作的检查工具。现在不是只说 claim 绑定了 citation，而是可以用 `inspect_report_trace.py` 从 report JSON 直接看到每个 claim 指向哪个 evidence、Verifier 的 atomic 判断是什么、Blue 是否执行过修复动作。

## 2026-06-27 Unified Agent Run Interface

### Background

项目早期目标里固定了 `BaseAgent.run(input, context) -> AgentResult`。代码里已经有 `BaseAgent` 和 `AgentResult`，但各 Agent 主要暴露 `plan/search/read/write/verify/review/repair` 等专用方法，统一入口没有完整覆盖。

### Problem

如果统一 Agent 协议只是存在于 base class，而实际 Agent 没有实现 `_run()`，外部框架无法稳定用同一种方式调用不同 Agent，也无法统一获得 ok/error/latency/metadata。

### Decision

给每个 Agent 增加轻量 `_run()` 适配层：

- 保留专用方法，不破坏 Coordinator。
- `run()` 用于框架统一编排和错误包装。
- 多参数 Agent 使用 dict input，字段清晰表达。
- BlueRepairAgent 也继承 BaseAgent，纳入多 Agent 协议。

### Implementation

- PlannerAgent：`run(question)`。
- SearcherAgent：`run(task)`。
- ReaderAgent：`run({"task": task, "results": results})`。
- WriterAgent：`run({"question": ..., "evidence": ..., "context": ..., "plan_type": ...})`。
- VerifierAgent：`run({"claim": claim, "evidence": evidence})`。
- CriticAgent：`run(report)`。
- BlueRepairAgent：`run({"report": report, "findings": findings})`。

### Validation

命令：

```powershell
uv run pytest tests/unit/test_agent_run_interface.py
uv run ruff check src tests scripts
```

结果：

- Agent run interface 测试：`4 passed`。
- invalid input 会返回 `AgentResult(ok=False)`。
- ruff passed。

### Interview Story

我保留了每个 Agent 的专用方法，保证模块语义清晰；同时补齐统一 `run()` 接口，让框架可以用同一种方式拿到 AgentResult，包括成功输出、错误、耗时和 metadata。这样既不牺牲代码可读性，又满足多 Agent 编排的一致接口。

## 2026-06-27 Runtime AgentResult Trace Integration

### Background

上一轮已经给每个 Agent 补齐了 `run()` 入口，但 Coordinator 的真实 pipeline 仍有一部分直接调用 `plan/search/read/write/verify/review/repair`。这会导致接口层和运行层脱节：单测能证明 AgentResult 可用，但一次完整研究运行里的 SQLite trace 不能证明所有 Agent 都经过统一协议。

### Problem

如果真实运行不走 `BaseAgent.run()`，后续排查问题时只能看到零散事件，无法统一追踪：

- 哪个 Agent 执行失败。
- 每个 Agent 花了多久。
- Agent 当时处于 planning/search/read/writing/verification/repair 哪个阶段。
- 这个事件对应哪个 task 或 claim。

### Decision

在 `ResearchCoordinator` 里增加 `_run_agent()` 小包装，所有实际 Agent 调用都通过它执行：

- `agent.run(input, AgentContext(...))` 返回 `AgentResult`。
- Coordinator 统一把 `ok/error/latency/metadata` 写入 SQLite `agent_events`。
- 失败时抛出异常，由原有任务 retry/block 机制处理。
- 保留各 Agent 的专用方法，方便单独测试和阅读。

### Implementation

- Planner、Searcher、Reader、Writer、Verifier、Critic、BlueRepair 都接入 `_run_agent()`。
- `AgentContext.metadata` 支持携带 `stage`、`task_id`、`claim_id`、`finding_count` 等调试信息。
- 集成测试检查一次 mock pipeline 后，SQLite 中至少包含 planner/searcher/reader/writer/verifier 事件。

### Validation

命令：

```powershell
uv run pytest tests/integration/test_mock_pipeline.py tests/unit/test_agent_run_interface.py
```

结果：

- 局部测试：`6 passed`。
- 完整 pipeline 仍能生成 report/evidence/vector index。
- SQLite agent_events 能真实看到多 Agent 执行轨迹。

### Interview Story

我没有只停留在“定义一个 AgentResult 类型”，而是把它接进 Coordinator 的真实运行路径。这样每个 Agent 的输出、错误、耗时和上下文 metadata 都会落到 SQLite，系统从“能跑”变成“能解释怎么跑、哪里出错、每一步花了多久”。

## 2026-06-27 Resume Evidence Traceability

### Background

项目已经形成能力结论，但结论不能脱离证据。每项能力都应该能反查到真实代码、测试、命令、实验产物和边界。

### Problem

原来的能力说明只列了模块级代码路径，比如 DAG/并发、记忆/检索、验证/修复。这个粒度不够细：

- 不知道一条 bullet 应该跑哪个命令来验证。
- 不知道对应哪些测试能证明它稳定。
- 不知道哪些产物能作为实验或学习证据。
- 不知道这条说法的边界在哪里，容易把 offline/mock 指标讲过头。

### Decision

新增一个可测试的 evidence registry，而不是只写一段 Markdown：

- `src/deepresearch_agent/resume_evidence.py` 保存结构化证据卡。
- `scripts/inspect_resume_evidence.py` 支持 `--list`、`--bullet`、`--json`。
- `docs/TRACEABILITY_MATRIX.md` 作为人工阅读版。
- 完成度检查要求该脚本、文档和测试存在。

### Implementation

每张证据卡包含：

- `resume_bullet`
- `code_paths`
- `tests`
- `commands`
- `artifacts`
- `learning_story`
- `boundary`

目前覆盖五类最终 bullet：orchestration、memory_vector、compression、verifier_redblue、evaluation。

### Validation

命令：

```powershell
uv run python scripts/inspect_resume_evidence.py --list
uv run python scripts/inspect_resume_evidence.py --bullet verifier_redblue
uv run pytest tests/unit/test_resume_evidence.py
```

### Interview Story

我把简历 bullet 做成了可追踪证据卡。复试时如果老师问“你说 Red-Blue 具体怎么实现”，我可以直接用 `inspect_resume_evidence.py --bullet verifier_redblue` 展示对应源码、测试、可运行命令、trace 产物和边界说明。这能避免空泛包装，也方便后续系统学习。

## 2026-06-27 Evaluation Output Directory Collision Fix

### Background

最终验收时并行跑了 ResearchBench 和 adversarial 两条 eval 命令。两条命令都在同一秒启动，而 `run_eval.py` 默认使用秒级时间戳作为目录名。

### Problem

默认输出目录原来是：

```text
reports/experiments/<YYYYMMDD_HHMMSS>/
```

并行运行时，两条评测可能写入同一个目录，导致 `metrics.json`、`summary.md`、`failure_cases.md` 互相覆盖或混淆。这会破坏实验可信度，尤其不利于后续复盘“这份 summary 到底来自 researchbench 还是 adversarial”。

### Decision

把默认 eval run id 从秒级升级为：

```text
<YYYYMMDD_HHMMSS_microseconds>_<suite>_<short_uuid>
```

例如：

```text
20260627_205012_123456_researchbench_a1b2c3d4
20260627_205012_654321_adversarial_e5f6a7b8
```

如果用户显式传入 `--experiment-dir`，仍然尊重用户指定路径。

### Implementation

- 新增 `build_eval_run_id(suite)`。
- `run_eval.py` 默认输出目录使用微秒级 run id，并追加 suite suffix 和短 uuid。
- 单测 `test_eval_run_id_uses_microseconds_and_suite_suffix` 防止退回秒级目录。

### Validation

命令：

```powershell
uv run pytest tests/unit/test_evaluation_runner.py
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,redblue,full
uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue
```

### Interview Story

这是一个真实工程细节：实验系统不仅要能算指标，还要保证产物不会互相污染。我在并行跑最终验收时发现秒级 timestamp 会撞目录，于是改成微秒级并带 suite 后缀，保证 ResearchBench 和 adversarial 的 summary/metrics/failure cases 可以被准确追溯。

## 2026-07-02 V3 Mechanism Hardening

### Background

另一个评估指出：项目已经接近图片里的 DeepResearch Agent，但如果想更像，需要补齐几个更硬的机制：9 状态状态机、timeout/replan/fallback、Red-Blue 收敛与震荡检测、benchmark domain 和 HotpotQA-style 多跳标注。

### Problem

V2 已经能跑完整链路，但一些简历上容易被追问的点还不够扎实：

- timeout 只是失败的一种，没有单独状态。
- replan/fallback 没有独立 trace。
- Red-Blue repair loop 只按轮数执行，没有收敛和震荡停止理由。
- ResearchBench 有 35 题，但缺少显式 domain 和 hotpot-style 子集统计。

### Decision

V3 不追求照抄图片中的数字，而是补真实可运行、可测试、可解释的机制：

- 新增 `TIMED_OUT`，形成 9 状态任务生命周期。
- Coordinator 记录 `fallback_level`、`replan_count`、`timed_out_tasks`、`batch_failure_events`。
- 新增 `RepairLoopTrace`，记录每轮 finding、weak claim、repair action、claim fingerprint 和 stop reason。
- Evaluation 增加 `repair_convergence_rate`、`repair_oscillation_rate`、`avg_repair_rounds`。
- ResearchBench 每题增加 `domain`、`required_hops`、`hotpot_style`。

### Implementation

- `TaskStatus.TIMED_OUT` 和状态机转移。
- Coordinator Level 1/2/3 降级 trace。
- `scripts/inspect_orchestration_failure.py`。
- `scripts/inspect_redblue_convergence.py`。
- `docs/learning_orchestration_fallback.md`。
- `docs/learning_redblue_convergence.md`。
- `docs/generated/day09_orchestration_failure_trace.md`。
- `docs/generated/day10_redblue_convergence_trace.md`。

### Validation

命令：

```powershell
uv run pytest
uv run ruff check src tests scripts
uv run python -m compileall src scripts tests
uv run python scripts/inspect_orchestration_failure.py --case batch_replan
uv run python scripts/inspect_redblue_convergence.py --case oscillation
```

结果：

- pytest：`94 passed, 3 skipped`。
- ruff passed。
- compileall passed。

### Interview Story

我把系统从“成功路径完整”推进到“失败路径也可观察”：timeout 有独立状态，batch failure 会记录 lightweight replan，证据不足会生成带 limitations 的 fallback report；Red-Blue 不再只是固定轮数，而是记录每轮 repair trace，并能判断收敛、震荡或达到最大轮数。

## 2026-07-02 V3 Formal Experiment Freeze

### Background

V3 机制已经补齐，但如果只说“实现了 9 状态、fallback、Red-Blue 收敛、domain/hotpot 评测”，仍然不够。项目最终要能复试讲清楚，就需要一组正式实验产物把这些机制固化下来。

### Problem

项目已经有 2026-06-27 的收尾实验，但那一轮还没有把 V3 新增字段完整纳入正式报告：

- `repair_convergence_rate`
- `repair_oscillation_rate`
- `avg_repair_rounds`
- `per_domain`
- `multi_hop_subset`
- `hotpot_style_subset`

此外，正式实验过程中还遇到一次历史 `vector_index_redblue.npz` 损坏 warning。如果这个 warning 没有被记录，以后复盘时会误以为实验环境不干净；如果实验因此失败，又说明项目对运行产物污染不够鲁棒。

### Decision

继续坚持 offline/mock 正式评测，不接服务器、不接真实 LLM：

- 服务器/GPU 对当前正式实验不是必需条件。
- 真实 LLM 会引入 API 成本、网络波动和不可复现输出。
- 当前阶段最重要的是证明本地机制、trace 和指标链路可复现。

同时将损坏 vector index warning 作为工程鲁棒性记录：系统按设计自动重建空 index 并继续运行，说明运行产物损坏不会阻塞正式实验。

### Implementation

执行两轮正式实验：

```powershell
uv run python scripts/run_eval.py --config configs/default.toml --experiments baseline,memory,compression,verifier,redblue,full --group-by domain
uv run python scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue --group-by domain
```

产物目录：

- `reports/experiments/20260702_162345_148429_researchbench_21c535de/`
- `reports/experiments/20260702_163315_852511_adversarial_f47f9b96/`

同步更新：

- `docs/EXPERIMENTS.md`
- `docs/FINAL_PROJECT_REPORT.md`
- `docs/TRACEABILITY_MATRIX.md`

### Validation

ResearchBench V3 主集：

- Cases：35。
- Domains：11。
- Multi-hop cases：13。
- Hotpot-style cases：6。
- `full.judge_score_mean`: 0.881。
- `full.repair_precision`: 0.886。
- `full.repair_coverage`: 1.000。
- `full.repair_convergence_rate`: 1.000。
- `full.repair_oscillation_rate`: 0.514。

Adversarial V3 suite：

- Cases：10。
- Multi-hop cases：7。
- `redblue.judge_score_mean`: 0.913。
- `redblue.repair_precision`: 0.933。
- `redblue.repair_coverage`: 1.000。
- `redblue.repair_oscillation_rate`: 0.300。

### Interview Story

V3 完成后，我没有只停留在“代码实现了机制”，而是重新跑了一轮正式离线实验，把 convergence、oscillation、domain、多跳和 Hotpot-style 子集全部纳入 summary。过程中遇到损坏 vector index，系统自动重建并继续运行，这也验证了我之前做的运行产物隔离和损坏恢复逻辑。最后我把结果写进实验文档和简历材料，并明确这些数字只代表 offline/mock benchmark 内部对比，不能包装成线上效果。

## 2026-07-02 Resume-Targeted Mechanism Gap Closing

### Background

对照目标简历项目后，项目还缺几类更容易被面试追问的硬机制：三层 JSON fallback、Red-Blue 修复前后成功率曲线、orchestration stress cases、backend smoke matrix 和写前 claim preflight。

### Problem

如果只说“支持多 Agent 和 Red-Blue”，还不够像真实工程。面试官可能会继续问：

- LLM 输出坏 JSON 怎么办？
- Red-Blue 到底修复前后提升多少？
- timeout/replan/fallback 只是代码里有，还是有压力样例？
- 多后端是能真实切，还是只写了类名？
- Writer 写作前有没有做重复 claim 和冲突 evidence 的防御？

### Decision

继续保持 offline/mock 默认，不用服务器，不把真实 LLM 放进主评测。先补可复现的小型机制实验：

- `StructuredOutputParser` 三层 fallback。
- 80 条 Red-Blue adversarial fixtures。
- `run_redblue_eval.py` 输出 before/after 成功率。
- `inspect_orchestration_stress.py` 输出 6 类压力样例。
- `run_backend_smoke_matrix.py` 输出 mock/openai/deepseek/vllm dry-run/smoke matrix。
- `ClaimPreflight` 在 Writer 前做去重、冲突提示和过强断言降级。

### Validation

新增固定结果：

- Structured JSON fallback：50 条 corrupted-output cases，parse_success_rate 1.000，Level 1/2/3 分布为 6/11/33。
- Red-Blue fixtures：80 条 adversarial fixtures，repair_success_before 0.425，repair_success_after 1.000，action_accuracy 1.000，repair_precision 1.000，repair_coverage 1.000。
- Orchestration stress：6 类固定失败路径，覆盖 task_timeout、retry_success、retry_exhausted、batch_replan、evidence_insufficient、global_fallback。
- Backend smoke matrix：默认只尝试 mock，真实后端无 key 时 dry-run，不访问网络。

### Interview Story

这一步不是为了照抄图片里的数字，而是把图片里容易被追问的“工程机制”补成真实可跑的小实验。我没有提前写 85% -> 95%，而是先构造 fixed fixtures 跑出真实 before/after；没有让真实 LLM 进入主评测，而是用 smoke matrix 记录后端可用性；JSON fallback 也用 50 条 corrupted cases 测 parse success。这样简历上的每个数字都能追到代码、测试和产物。

## 2026-07-02 Final Sprint Evidence Pack

**背景**

对标图片简历时，项目已经具备 V3 主机制，但还需要更硬的“作品证据”：更多 Red-Blue fixtures、更完整 JSON fallback 统计、可选 LLM-as-Judge smoke，以及一键最终实验入口。

**遇到的问题**

- 原有 Red-Blue fixtures 只有 40 条，能证明动作规则，但不够支撑“成功率曲线”。
- Structured JSON fallback 只有 30 条 case，summary 只给总成功率，缺少 strict/fallback/schema repair 细分。
- 后端 smoke matrix 存在，但缺少单独的 LLM-as-Judge smoke 入口。
- 最终产物分散在多个脚本里，复现实验时需要手动记很多命令。

**方案**

- 将 Red-Blue fixtures 扩展到 80 条，新增 `source_of_error` 维度，并输出 per-failure-mode / per-source-of-error 表。
- 将 structured output cases 扩展到 50 条，summary 增加 strict parse success、fallback parse success、schema repair warning。
- 新增 `run_real_judge_smoke.py`，mock 默认可跑，真实 DeepSeek/OpenAI 只有显式 `--run-real` 且有 key 时才请求。
- 新增 `run_final_experiments.py`，把 showcase、ResearchBench、adversarial、Red-Blue fixture eval、JSON fallback eval、backend smoke、judge smoke、completion check 打成一个 final evidence pack。

**验证结果**

- Red-Blue fixtures：80 条，repair_success_before 0.425，repair_success_after 1.000，action_accuracy 1.000，repair_precision 1.000，repair_coverage 1.000。
- Structured JSON fallback：50 条，parse_success_rate 1.000，Level 1/2/3 分布 6/11/33。
- `run_final_experiments.py --skip-eval` 可生成 final evidence pack 骨架。

**为什么这样做**

这一步仍然坚持 offline/mock 默认。真实 LLM judge 和 provider smoke 只证明接口可用，不进入正式 ResearchBench 指标，避免 API 波动、成本和模型变化污染可复现实验。

## 2026-07-02 Low-Cost DeepSeek Real API Showcase

**背景**

为了让项目更接近 AI Agent / AI 应用实习的投递材料，需要证明它不只是 mock/offline demo，也具备真实大模型后端接入和成本控制意识。

**方案**

- 将 DeepSeek 默认模型从旧兼容名切换为 `deepseek-v4-flash`。
- 在 `LLMBackendConfig` 中增加 `max_tokens`，DeepSeek 默认限制为 512。
- 为 DeepSeek token usage 增加估算成本字段，区分 prompt cache hit、cache miss 和 output token。
- 新增 `scripts/run_deepseek_showcase.py`，只有显式 `--run-real` 且存在 `DEEPSEEK_API_KEY` 时才调用真实 API。
- 真实 API showcase 输出到 `reports/real_api/deepseek_showcase.md`，并明确不混入 offline/mock benchmark。

**验证**

- `uv run pytest tests/unit/test_llm_factory.py tests/unit/test_backend_smoke_matrix.py tests/unit/test_real_judge_smoke.py tests/integration/test_showcase.py`
- `uv run python scripts/inspect_llm_backend.py --backend deepseek --json`
- `uv run python scripts/run_deepseek_showcase.py --json --output reports/real_api/deepseek_showcase_dryrun.json`

**面试讲法**

正式评测仍然使用离线 mock，保证可复现；真实 DeepSeek 只作为低成本 provider showcase，说明系统已经具备 OpenAI-compatible 后端接入、token/cost 记录和 API key 环境变量管理能力。

## 2026-07-02 FastAPI Local Demo App

**背景**

项目已经有完整的 Markdown/JSON evidence pack，但投递 AI 应用实习时，面试官更容易被“能打开、能运行、能看到链路”的作品打动。因此在不重写 Agent 内核的前提下补一个本地 Web Demo。

**方案**

- 新增 FastAPI + 静态 HTML/CSS/JS Demo，入口为 `scripts/run_demo_server.py`。
- 默认加载 `reports/final/final_sprint_check/showcase/`，页面分为 Overview、Plan DAG、Report、Evidence & Memory、Verification & Repair。
- 新问题通过 `/api/runs` 启动 mock/offline run，后台复用 `build_showcase()`，前端轮询 `/api/runs/{run_id}` 和 artifacts。
- DeepSeek 单独放在 `/api/deepseek-showcase`，只有显式 `run_real=true` 且存在 key 时才请求真实 provider。

**验证**

- `uv sync --extra dev`
- `uv run pytest tests/integration/test_web_demo.py`
- `uv run ruff check src/deepresearch_agent/web tests/integration/test_web_demo.py scripts/run_demo_server.py`

**面试讲法**

这个 Demo 不是另起炉灶做一个 toy app，而是把已有可复现 Agent 链路产品化展示：默认 evidence pack 保证演示稳定，新问题 mock run 展示系统可运行，DeepSeek provider smoke 展示真实后端接入和成本边界。

## 2026-07-04 Resume Gap Closing Pack

**背景**

对标图片简历后，项目已经有 70%-80% 的效果，但仍需要补三类材料：本地知识库 RAG 真实感、LLM/NLI 式二级 verifier 证据、以及更招聘友好的评测与投递包装。

**方案**

- 新增 `corpus_profiles.py` 和 `scripts/build_corpus_profiles.py`，支持从本地 Markdown/TXT/HTML 构建 Searcher-compatible JSONL corpus。
- Web Demo 新增 corpus profile 选择，`/api/corpus-profiles` 暴露 `offline_agent_docs`、`resume_agent_docs`、`paper_reading_docs` 三个场景。
- 新增 `llm_verifier_smoke.py` 和 `scripts/run_llm_verifier_smoke.py`，默认 dry-run，真实 DeepSeek 只有显式 `--run-real` 才调用。
- 新增 60 题 `researchbench_extended.jsonl`，五类 answer_type 各 12 题，并跑通 full profile 离线评测。
- 新增 `scripts/inspect_resume_metrics.py`，把数据集覆盖、产物存在性和简历指标名称聚合成投递检查入口。

**验证**

- `uv run python scripts/build_corpus_profiles.py`
- `uv run python scripts/run_llm_verifier_smoke.py --json`
- `uv run python scripts/inspect_resume_metrics.py --json`
- `uv run python scripts/run_eval.py --dataset data/benchmarks/researchbench_extended.jsonl --suite researchbench --experiments full --group-by domain`
- `uv run pytest tests/unit/test_corpus_profiles.py tests/integration/test_web_demo.py tests/unit/test_llm_verifier_smoke.py tests/unit/test_extended_benchmark.py`

**面试讲法**

这一步补的是“真实感”和“可讲性”：知识库 profile 让项目更像企业 RAG 应用；LLM verifier smoke 回答“heuristic verifier 不够怎么办”；extended ResearchBench 已跑 60 题 full profile，judge mean 0.881、repair_precision 0.947、repair_coverage 1.000，但尚未补 baseline ablation，避免夸大成完整提升实验。
