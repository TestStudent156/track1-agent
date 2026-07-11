# Track 1: Hybrid Token-Efficient Routing Agent

## Track Name
**Hybrid Token-Efficient Routing Agent** (Beginner Friendly · AI Agent Track)

## Core Objective
Build an AI agent that completes a fixed set of tasks autonomously, **deciding in real time which Fireworks AI model is the cheapest one that can still answer accurately**. The goal: **use the fewest tokens possible, without falling below the accuracy threshold**.

## Key Principles

### Scoring
- **Dual metric:** Token count + output accuracy
- **Accuracy gate first** — must pass threshold to be ranked
- **Then ranked by token efficiency** — fewer tokens = higher rank
- Only inference routed through Fireworks AI (`FIREWORKS_BASE_URL`, using a model from `ALLOWED_MODELS`) is scored

### Routing Intelligence Wins
- **"picking the cheapest sufficient Fireworks model for each task — wins, not raw compute power"**
- The agent must evaluate each query and pick the optimal model
- This is NOT about having the biggest model — it's about having the smartest routing

### Local Models
- Optional, only useful for development/testing
- Inference run locally is NOT tracked and does NOT count toward score
- Only calls through Fireworks AI (FIREWORKS_BASE_URL, using ALLOWED_MODELS) are scored

### Fine-Tuning Allowed
- "Prompt-based and fine-tuned approaches are scored exactly the same way: token count and output accuracy"
- Can fine-tune the router model for better routing decisions

## Suggested Build: Model Router / Cost Optimizer
A routing layer that reads each query and instantly picks the cheapest, best-suited model from the available endpoints.

## 8 Task Categories (from Participant Guide)
1. **Factual Knowledge** — Concepts, definitions, how things work
2. **Mathematical Reasoning** — Multi-step arithmetic, percentages, word problems
3. **Sentiment Classification** — Labelling sentiment + justifying
4. **Text Summarisation** — Condensing passages to specific format/length
5. **Named Entity Recognition** — Extracting & labelling entities (person, org, location, date)
6. **Code Debugging** — Finding bugs + corrected implementations
7. **Logical / Deductive Reasoning** — Constraint-based puzzles
8. **Code Generation** — Writing correct functions from spec

## Environment Variables (runtime — DO NOT hardcode)
- `FIREWORKS_API_KEY` — API key from harness
- `FIREWORKS_BASE_URL` — ALL Fireworks calls must go through this URL
- `ALLOWED_MODELS` — Comma-separated model IDs, published on launch day

## Docker I/O
- Input: `/input/tasks.json` → `[{"task_id": "t1", "prompt": "..."}]`
- Output: `/output/results.json` → `[{"task_id": "t1", "answer": "..."}]`

## Rules
- Exit code 0 on success
- Max runtime: 10 minutes
- Only ALLOWED_MODELS permitted
- All API calls through FIREWORKS_BASE_URL
- No hardcoding/caching answers
- Image ≤ 10GB, linux/amd64 manifest
- 10 submissions/hour per team

## Architecture Strategy: Smart Router

```
tasks.json → [Task Classifier] → [Model Router] → [Fireworks API Call] → [Answer] → results.json
                ↑                       ↑
        Detects category       Picks cheapest
        from 8 types           sufficient model
```

### Router Logic Per Category (hypothesis — adjust at runtime based on ALLOWED_MODELS)
| Category | Strategy |
|----------|----------|
| Factual Q&A | Smaller model likely sufficient |
| Math Reasoning | Larger model with step-by-step reasoning |
| Sentiment Classification | Smaller model — simple classification |
| Summarization | Mid-tier model — compression task |
| NER | Mid-tier — structured extraction |
| Code Debugging | Larger model — needs code understanding |
| Logic Puzzles | Largest model — complex reasoning |
| Code Generation | Larger model — needs strong code capability |

### Token Optimization Strategies
1. **Minimize system prompt** — shorter instructions = fewer input tokens
2. **No chain-of-thought in output** — answer directly, reasoning tokens count
3. **Category-specific prompts** — tailored per task type, not generic
4. **Model selection by complexity** — don't use a 70B model for sentiment classification
5. **Batch similar tasks** — if same category, reuse prompt template with minimal variation
6. **No unnecessary context** — only pass the task prompt, no extra preamble
