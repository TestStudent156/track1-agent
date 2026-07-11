VIDEO PRESENTATION SCRIPT
==========================
Duration: 60-90 seconds
Format: Screen recording with voiceover (Loom / OBS)

## SCENE 1: Hook (0:00 - 0:10)
[Show cover image / project logo]
Voiceover: "Hi, I'm presenting the Hybrid Token-Efficient Routing Agent for AMD Hackathon ACT II Track 1. 
It answers one question: how do you route AI tasks to the cheapest capable model — without wasting tokens on routing itself?"

## SCENE 2: The Problem (0:10 - 0:25)
[Show slide 2 - "The Problem"]
Voiceover: "Every token costs money. If you send a simple sentiment analysis to a code-generation model, 
you burn 5x the tokens. And using a second LLM just to decide which model to use? That's 50-200 wasted 
tokens before you even start solving the problem."

## SCENE 3: Architecture (0:25 - 0:45)
[Show slide 3 - Pipeline, animated arrows]
Voiceover: "Our solution is a three-step pipeline. First, a zero-token regex classifier reads the prompt 
and categorizes it into one of 8 categories — fact, math, sentiment, summarization, NER, code debug, 
logic, or code generation. No API call. Less than 1 millisecond.

Then, an empirical routing table — built from real benchmark runs — picks the cheapest model for that 
category. kimi-k2p7-code handles 7 categories, minimax-m3 is reserved for NER where it delivers clean 
JSON at just 256 tokens."

## SCENE 4: Results (0:45 - 1:05)
[Show slide 5 - Token Optimization, highlight numbers]
Voiceover: "The results speak for themselves. Across 8 representative tasks, the total is just 4,769 tokens. 
That includes a code debug at 1,126 and logic reasoning at 1,691 — the heavy tasks. Runtime is under 40 
seconds, the Docker image is 152 megabytes, and we hit 8 out of 8 tasks correctly.

Key optimizations: JSON mode for sentiment and NER prevents reasoning tokens from leaking out. 
Category-specific max_tokens caps. And of course, the zero-token regex classifier."

## SCENE 5: Deployment & Close (1:05 - 1:20)
[Show slide 6 - Results & Deployment]
Voiceover: "The agent runs entirely in Docker. It reads tasks from /input/tasks.json and writes results 
to /output/results.json. No hardcoded model IDs — it reads ALLOWED_MODELS at runtime, so it adapts 
to whatever models the harness provides. The image is on Docker Hub ready to pull."

[Show slide 7 - Thank You]
Voiceover: "Thank you. Hybrid Token-Efficient Routing Agent — maximum accuracy, minimum tokens."

---

RECORDING SETUP:
- Tool: Loom (free) or OBS Studio
- Record the slides.html in a full-screen browser
- Use arrow keys or scroll to advance slides
- Record voiceover separately or use Loom's built-in mic
- Export as MP4, keep under 100 MB for upload