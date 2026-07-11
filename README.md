# 🏆 AMD Developer Hackathon ACT II — Track 1

## Hybrid Token-Efficient Routing Agent

An AI agent that classifies tasks across **8 categories** and routes each to the **cheapest sufficient Fireworks AI model** — minimizing token usage while maintaining accuracy. Uses a **zero-token regex classifier** (no LLM call for routing) and an **empirical routing table** built from real benchmark runs.

### Allowed Models (Track 1)

| Model | Tier | Best For |
|-------|------|----------|
| `minimax-m3` | Budget | NER (clean JSON, 256 tokens) |
| `kimi-k2p7-code` | Premium | 7 categories — factual, math, sentiment, summarize, code-debug, logic, code-gen |
| `gemma-4-31b-it` | Mid | Fallback / general |
| `gemma-4-26b-a4b-it` | Mid | Fallback / general |
| `gemma-4-31b-it-nvfp4` | Mid | Fallback / general |

### Routing Strategy

```
kimi-k2p7-code  →  factual, math, sentiment, summarize, code_debug, logic, code_gen
minimax-m3      →  ner
gemma-4-31b-it  →  fallback (if kimi or minimax unavailable)
gemma-4-26b-a4b-it → fallback
gemma-4-31b-it-nvfp4 → fallback
```

## 📊 Results (8 Test Tasks)

| Category | Model | Tokens |
|----------|-------|--------|
| factual | kimi-k2p7-code | 271 |
| math | kimi-k2p7-code | 233 |
| sentiment | kimi-k2p7-code | 295 |
| summarize | kimi-k2p7-code | 451 |
| ner | minimax-m3 | 256 |
| code_debug | kimi-k2p7-code | 1,126 |
| logic | kimi-k2p7-code | 1,691 |
| code_gen | kimi-k2p7-code | 446 |
| **Total** | | **~4,769** |

- ✅ **8/8 tasks correct**
- ✅ **Exit code 0**
- ✅ **~40s runtime**
- ✅ **152 MB Docker image**

## 🏗️ Architecture

```
Input Task → Regex Classifier → Empirical Router → Fireworks Model → JSON Output
   (0 tokens)   (<1ms, word-boundary)   (benchmark-built)   (single call)   (validated)
```

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python agent.py
# Reads input/tasks.json → writes output/results.json
```

## 🐳 Docker Build & Test

```bash
docker build --platform linux/amd64 -t track1-agent:latest .

docker run --rm \
  -e FIREWORKS_API_KEY="fw_..." \
  -e FIREWORKS_BASE_URL="https://api.fireworks.ai/inference/v1" \
  -e ALLOWED_MODELS="minimax-m3,kimi-k2p7-code,gemma-4-31b-it,gemma-4-26b-a4b-it,gemma-4-31b-it-nvfp4" \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  track1-agent:latest
```

## 🔄 GitHub Actions CI/CD

Automated Docker build and test on every push. See [`.github/workflows/docker-build-test.yml`](.github/workflows/docker-build-test.yml).

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `FIREWORKS_API_KEY` | API key (injected by harness) |
| `FIREWORKS_BASE_URL` | `https://api.fireworks.ai/inference/v1` |
| `ALLOWED_MODELS` | Comma-separated: `minimax-m3,kimi-k2p7-code,gemma-4-31b-it,gemma-4-26b-a4b-it,gemma-4-31b-it-nvfp4` |

## 📁 Project Structure

```
├── agent.py              # Main agent
├── dockerfile            # Docker image
├── entrypoint.sh         # Container entry point
├── requirements.txt      # Python deps
├── .github/workflows/    # CI/CD
├── lablab-assets/        # Cover, slides, video
├── input/tasks.json      # Sample tasks
└── README.md
```

## ⚡ Token Optimizations

1. **Zero-token classifier** — regex with word boundaries, no API call
2. **Empirical routing** — benchmark-built table, not LLM-based
3. **JSON response_format** — for sentiment + NER (blocks thinking tokens)
4. **Category-specific max_tokens** — 200 (sentiment) up to 3000 (logic)
5. **temperature=0.0** — deterministic, no variance waste
6. **Single API call per task** — no multi-turn conversations
7. **Fallback on empty response** — retry with most reliable model
