# Showcase LLM Backend

Backend: `deepseek`
Model: `deepseek-v4-flash`
Base URL: `https://api.deepseek.com`
Timeout seconds: `60.0`
Max retries: `2`
Env var: `DEEPSEEK_API_KEY`
Env configured: `true`
Offline safe: `false`

## Run Summary Backend Fields

- llm_backend: `deepseek`
- model: `deepseek-v4-flash`
- llm_timeout_seconds: `60.0`
- llm_max_retries: `2`
- llm_vllm_base_url: `http://localhost:8000/v1`
- corpus_path: `data/corpus/offline_corpus.jsonl`

The showcase records backend configuration, but offline/mock benchmark metrics must not be mixed with real LLM outputs.