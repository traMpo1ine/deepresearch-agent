# Week 08-14: Trust, Evaluation, Backends, Blog

后半程目标是把系统从“能生成报告”推进到“能验证、能修复、能评测、能讲清楚”。

重点模块：

- Writer：结构化报告、sections、claims、citations、limitations。
- Verifier：SUPPORTED / PARTIAL / UNSUPPORTED / CONTRADICTED 和 verification trace。
- Red-Blue：AttackFinding 与 ADD / DELETE / MODIFY / VERIFY 修复动作。
- ResearchBench：35题离线评测集。
- LLM-as-Judge：factuality、coverage、citation_quality、structure、usefulness。
- 统计评测：Bootstrap 95% CI、Cohen's d。
- LLM 后端：Mock、OpenAI-compatible、DeepSeek、vLLM。

当前代码入口：

- `src/deepresearch_agent/agents/writer.py`
- `src/deepresearch_agent/agents/verifier.py`
- `src/deepresearch_agent/redblue/`
- `src/deepresearch_agent/evaluation/`
- `src/deepresearch_agent/llm/`
- `scripts/run_eval.py`
