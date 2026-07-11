# AMD Developer Hackathon (ACT II) — Participant Submission Guide

## Track 1: General-Purpose AI Agent

### What you are building
An AI agent that handles a wide variety of natural language tasks across multiple capability domains, using Fireworks AI models as efficiently as possible.

### Capability categories (8 total)

| # | Category | What it covers |
|---|----------|----------------|
| 1 | Factual Knowledge | Explaining concepts, definitions, and how things work |
| 2 | Mathematical Reasoning | Multi-step arithmetic, percentages, word problems, projections |
| 3 | Sentiment Classification | Labelling sentiment and justifying the classification |
| 4 | Text Summarisation | Condensing passages to a specific format or length constraint |
| 5 | Named Entity Recognition (NER) | Extracting and labelling entities (person, org, location, date) |
| 6 | Code Debugging | Identifying bugs in code snippets and providing corrected implementations |
| 7 | Logical / Deductive Reasoning | Constraint-based puzzles where all conditions must be satisfied |
| 8 | Code Generation | Writing correct, well-structured functions from a spec |

### What to submit
A Docker image pushed to a public registry (e.g. GitHub Container Registry, Docker Hub).

### Container I/O
1. Read tasks from `/input/tasks.json` on startup:
   ```json
   [{"task_id": "t1", "prompt": "Summarise the following text in one sentence: ..."}, {"task_id": "t2", "prompt": "..."}]
   ```
2. Write results to `/output/results.json` before exiting:
   ```json
   [{"task_id": "t1", "answer": "..."}, {"task_id": "t2", "answer": "..."}]
   ```

### Environment Variables (injected at runtime — DO NOT hardcode)
- `FIREWORKS_API_KEY` — Provided by the harness — use this key, not your own
- `FIREWORKS_BASE_URL` — Base URL for all Fireworks API calls — must be used to configure your client
- `ALLOWED_MODELS` — Comma-separated list of permitted Fireworks AI model IDs, published on launch day

### Critical Rules
- All API calls must go through `FIREWORKS_BASE_URL`. Calls that bypass this URL will not be recorded and the submission will score zero tokens.
- Do not hardcode model IDs: read from `ALLOWED_MODELS` at runtime.
- Exit code 0 on success, non-zero on failure
- Maximum runtime: 10 minutes
- Only models in `ALLOWED_MODELS` are permitted, calls to other models invalidate the submission
- `/output/results.json` must be valid JSON, malformed output scores zero
- Local models and tokens used locally count as zero for the final score; all inference must go through Fireworks AI via `FIREWORKS_BASE_URL`
- Do not hardcode or cache answers; evaluation uses unseen prompt variants
- Image compressed size must not exceed 10GB — larger images are rejected before pulling
- Submissions are rate-limited to 10 per hour per team

### Scoring
1. **Accuracy gate**: LLM-Judge evaluates each answer against the expected intent. Submissions below the accuracy threshold are excluded from the leaderboard.
2. **Token efficiency**: submissions that pass the accuracy gate are ranked ascending by total tokens recorded by the judging proxy. Fewer tokens = higher rank.

---

## Track 2: Video Captioning Agent

### What you are building
An AI agent that watches a video clip and generates a caption in a requested style.

### Styles to support
- **formal** — Professional, objective, factual tone
- **sarcastic** — Dry, ironic, lightly mocking
- **humorous_tech** — Funny, with technology or programming references
- **humorous_non_tech** — Funny, everyday humour with no technical jargon

### Container I/O
1. Read from `/input/tasks.json`:
   ```json
   [{"task_id": "v1", "video_url": "https://storage.example.com/clips/clip1.mp4", "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]}]
   ```
2. Write to `/output/results.json`:
   ```json
   [{"task_id": "v1", "captions": {"formal": "...", "sarcastic": "...", "humorous_tech": "...", "humorous_non_tech": "..."}}]
   ```

### Environment
No API key or model restriction. You may call any model, API, or framework: use your own credentials inside the container.

### Example Clips
- v1: Urban autumn boulevard with golden trees and city traffic — `https://storage.googleapis.com/amd-hackathon-clips/1860079-uhd_2560_1440_25fps.mp4`
- v2: Orange kitten among green foliage in a garden — `https://storage.googleapis.com/amd-hackathon-clips/13825391-uhd_3840_2160_30fps.mp4`
- v3: Office worker at a desktop computer in a modern open-plan office — `https://storage.googleapis.com/amd-hackathon-clips/3044693-uhd_3840_2160_24fps.mp4`

### Scoring
- Caption accuracy (0–1): how faithfully the caption reflects the video content
- Style match (0–1): how well the caption matches the requested tone
- Final score = weighted average across all clips and all four styles

---

## Track 3: Unicorn (Open Innovation)

### What you are building
An original AI application that uses AMD compute resources.

### What to submit
- GitHub repository URL — Required
- Demo video — Required
- Slide deck (PDF) — Required
- Live demo / hosted URL — Optional but recommended

No Docker image required. AMD compute usage is a requirement: projects that do not demonstrate it will be disqualified.

---

## General Rules (All Tracks)
- Container must start and be ready within 60 seconds
- Response time per request must be under 30 seconds
- All responses must be in English
- Do not hardcode or cache answers to specific inputs — evaluation uses unseen variants
- Container images must be publicly pullable at submission time

## Image Architecture Requirement
The judging VM runs `linux/amd64`. Your image must include a `linux/amd64` manifest or it will fail to pull and score zero.

If you build on Apple Silicon (M1/M2/M3), add `--platform linux/amd64` to your build command:
```bash
docker buildx build --platform linux/amd64 --tag your-image:latest --push .
```
