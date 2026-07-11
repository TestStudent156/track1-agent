# 🏆 AMD Developer Hackathon ACT II — Track 1

## Hybrid Token-Efficient Routing Agent

An AI agent that classifies tasks across 8 categories and routes each to the **cheapest sufficient Fireworks AI model** — minimizing token usage while maintaining accuracy.

---

## 📁 Project Structure

```
HackathonAMDII/
├── agent.py              # Main agent: classify → route → call → output
├── Dockerfile            # linux/amd64 Docker image definition
├── entrypoint.sh         # Container entry point
├── requirements.txt      # Python dependencies (minimal!)
├── .env.example          # Template for local dev (DO NOT include in image)
├── .dockerignore         # Excludes dev files from Docker build
├── input/
│   └── tasks.json        # Sample test tasks (all 8 categories)
├── output/
│   └── .gitkeep          # Placeholder for output directory
├── Participant_Guide_AMD_Hackathon_ACT_II.md   # Full hackathon guide
├── Track1_Specification.md                     # Track 1 spec summary
└── README.md             # This file
```

## 🏗️ Architecture

```
                    ┌──────────────────────┐
                    │   Task Classifier     │  Keyword-based detection
                    │   (8 categories)      │  → sentiment, factual, math,
                    └──────────┬───────────┘     ner, summarize, code_debug,
                               │                 code_gen, logic
                    ┌──────────▼───────────┐
                    │   Model Router        │  Picks cheapest model from
                    │   (Cost Optimizer)    │  ALLOWED_MODELS that meets
                    └──────────┬───────────┘  the tier requirement
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Tier 1 Small │ │ Tier 2 Mid   │ │ Tier 3 Large │
     │ Sentiment    │ │ Summarize    │ │ Math         │
     │ Factual      │ │ NER          │ │ Logic        │
     └──────┬───────┘ └──────┬───────┘ │ Code Debug   │
            │                │         │ Code Gen     │
            └────────────────┼─────────┘
                             ▼
                    ┌──────────────────┐
                    │  Fireworks API   │  Single call per task
                    │  (BASE_URL)      │  via FIREWORKS_BASE_URL
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │  results.json    │  [{task_id, answer}]
                    └──────────────────┘
```

## 🚀 Quick Start (Local Dev)

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your Fireworks API credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run locally
python agent.py
# → Reads input/tasks.json, writes output/results.json
```

## 🐳 Docker Build & Test

```bash
# Build for linux/amd64 (required by judging VM)
docker buildx build --platform linux/amd64 -t track1-agent:latest .

# Run with environment variables (simulates harness injection)
docker run --rm \
  -e FIREWORKS_API_KEY="your_key" \
  -e FIREWORKS_BASE_URL="https://api.fireworks.ai/inference/v1" \
  -e ALLOWED_MODELS="accounts/fireworks/models/glm-5p2,accounts/fireworks/models/llama-v3p1-8b-instruct" \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  track1-agent:latest
```

## 📤 Submitting

```bash
# Tag and push to a public registry
docker buildx build --platform linux/amd64 \
  -t ghcr.io/yourusername/track1-agent:latest \
  --push .
```

## 🔑 Environment Variables (injected by harness at runtime)

| Variable | Description |
|----------|-------------|
| `FIREWORKS_API_KEY` | API key provided by harness |
| `FIREWORKS_BASE_URL` | Base URL — ALL calls must go through this |
| `ALLOWED_MODELS` | Comma-separated Fireworks model IDs |

## ⚡ Token Optimization Strategies

1. **Smart routing** — small models for simple tasks (sentiment, factual)
2. **Minimal prompts** — category-specific, no generic boilerplate
3. **No chain-of-thought in output** — answer directly, reasoning tokens count
4. **temperature=0.0** — deterministic, no wasted tokens on variance
5. **max_tokens cap** — prevents runaway responses
6. **Single API call per task** — no multi-turn conversations

## 📋 Rules Checklist

- [x] Exit code 0 on success
- [x] Max runtime 10 minutes
- [x] Only ALLOWED_MODELS used
- [x] All calls through FIREWORKS_BASE_URL
- [x] No hardcoded answers
- [x] Valid JSON output
- [x] linux/amd64 manifest
- [x] Image < 10GB
