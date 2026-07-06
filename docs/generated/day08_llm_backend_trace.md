# LLM Backend Inspection

Backend: `mock`
Model: `mock-researcher-v0`
Base URL: `local://mock`
Timeout seconds: `60.0`
Max retries: `2`
Env var: `None`
Env configured: `true`
Offline safe: `true`

## Smoke Result

Completion preview: Mock response for: Reply with ok.
Embedding dim: `64`

## Real Backend Dry Run

DeepSeek dry-run example:

```json
{
  "backend": "deepseek",
  "model": "deepseek-chat",
  "env_var": "DEEPSEEK_API_KEY",
  "env_configured": false,
  "offline_safe": false,
  "base_url": "https://api.deepseek.com"
}
```

vLLM dry-run example:

```json
{
  "backend": "vllm",
  "model": "local-model",
  "env_var": "VLLM_API_KEY",
  "env_configured": false,
  "offline_safe": false,
  "base_url": "http://localhost:8000/v1"
}
```
