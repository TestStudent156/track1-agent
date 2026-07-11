#!/usr/bin/env python3
"""
AMD Developer Hackathon ACT II — Track 1
Hybrid Token-Efficient Routing Agent

Reads tasks from /input/tasks.json, classifies each task into one of 8 categories,
routes to the cheapest sufficient Fireworks AI model, and writes results to /output/results.json.

Token optimization is the #1 priority after accuracy.

Official allowed models (Track 1):
  minimax-m3         — cheapest ($0.3/$1.2 per M), good for simple tasks
  gemma-4-26b-a4b-it — 26B, mid-tier
  gemma-4-31b-it     — 31B, mid-tier
  gemma-4-31b-it-nvfp4 — 31B NVFP4, mid-tier
  kimi-k2p7-code     — code specialist ($0.95/$4 per M), most reliable for complex tasks
"""

import os
import re
import json
import sys
import logging
from typing import Optional
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration — ALL from environment, nothing hardcoded
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
BASE_URL = os.environ.get("FIREWORKS_BASE_URL", "")
ALLOWED_MODELS = [m.strip() for m in os.environ.get("ALLOWED_MODELS", "").split(",") if m.strip()]

INPUT_PATH = os.environ.get("INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "/output/results.json")

# Fallback paths for local dev on Windows
if not os.path.exists(INPUT_PATH):
    INPUT_PATH = os.path.join(os.path.dirname(__file__), "input", "tasks.json")
if not os.path.exists(os.path.dirname(OUTPUT_PATH)):
    OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "results.json")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("router")

# ---------------------------------------------------------------------------
# OpenAI-compatible client → Fireworks AI
# default_headers with User-Agent bypasses Cloudflare 1010 browser fingerprint check
# ---------------------------------------------------------------------------
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    default_headers={"User-Agent": "fireworks-routing-agent/1.0"},
)

# ---------------------------------------------------------------------------
# 1. TASK CLASSIFIER — detect category from prompt text (word-boundary aware)
# ---------------------------------------------------------------------------

CATEGORY_PATTERNS = {
    "sentiment": [
        r"\bsentiment\b", r"\bemotion\b", r"\bfeeling\b", r"\btone\b",
        r"\bpositive\b", r"\bnegative\b", r"\bmood\b", r"\bopinionated\b",
        r"overall sentiment",
    ],
    "ner": [
        r"\bentit(y|ies)\b", r"\bnamed entity\b", r"\bner\b",
        r"extract (persons?|organizations?|locations?|dates?)",
        r"persons?,\s*organizations?",
    ],
    "summarize": [
        r"\bsummari[sz]e\b", r"\bsummary\b", r"\bcondense\b",
        r"\btldr\b", r"\bt-l;dr\b", r"\babridge\b", r"\bshorten\b",
    ],
    "code_debug": [
        r"\bdebug\b", r"\bbug\b", r"\bfix the (code|bug)\b",
        r"\berror in\b", r"\bwhat'?s wrong\b",
        r"\bincorrect\b", r"\bdoesn'?t work\b", r"\bfails\b", r"\bexception\b",
    ],
    "code_gen": [
        r"\bwrite a function\b", r"\bwrite code\b", r"\bimplement\b",
        r"\bgenerate code\b", r"\bcreate a function\b",
        r"\bpython function\b", r"\bjavascript function\b",
        r"\bwrite a program\b", r"\bcode that\b",
        r"\bfunction that returns\b",
    ],
    "math": [
        r"\bcalculat(e|ion|ed)\b", r"\bcomput(e|ation|ed)\b", r"\bsolve\b",
        r"\bmath\b", r"\barithmetic\b", r"\bpercentage\b",
        r"\bsum of\b", r"\bproduct of\b", r"\bdivide\b", r"\bmultiply\b",
        r"\bequation\b", r"\bhow many\b", r"\btotal cost\b", r"\bprobability\b",
        r"\bdiscount\b", r"\bprice\b", r"\$\d+", r"\d+%",
        r"\binterest\b", r"\brate\b", r"\bprofit\b", r"\bloss\b",
    ],
    "logic": [
        r"\bif and only if\b", r"\bconstraint\b", r"\bpuzzle\b",
        r"\blogic\b", r"\bdeduce\b", r"\breasoning\b",
        r"\bmust be\b", r"\bcannot be\b", r"\bwho is\b",
        r"\bwhich person\b", r"\barrange\b", r"\bschedule\b",
        r"\bseating\b",
    ],
    "factual": [
        r"\bwhat is\b", r"\bexplain\b", r"\bdefin(e|ition)\b",
        r"\bhow does\b", r"\bdescribe\b", r"\bwhat are\b",
        r"\bwho was\b", r"\bwhen did\b", r"\bhistory of\b",
    ],
}


def classify_task(prompt: str) -> str:
    """
    Classify a task prompt into one of 8 categories using word-boundary regex matching.
    Falls back to 'factual' if no clear match.
    """
    prompt_lower = prompt.lower()

    # Special case: code_debug requires both a debug keyword AND code context
    debug_keywords = CATEGORY_PATTERNS["code_debug"]
    code_context = (
        "code" in prompt_lower or "function" in prompt_lower
        or "def " in prompt_lower or "```" in prompt_lower
        or "return " in prompt_lower or "print(" in prompt_lower
        or "class " in prompt_lower
    )
    if any(re.search(pat, prompt_lower) for pat in debug_keywords) and code_context:
        return "code_debug"

    # Check remaining categories in priority order
    for category in ["code_gen", "sentiment", "ner", "summarize", "math", "logic", "factual"]:
        patterns = CATEGORY_PATTERNS[category]
        if any(re.search(pat, prompt_lower) for pat in patterns):
            return category

    return "factual"


# ---------------------------------------------------------------------------
# 2. MODEL ROUTER — empirically optimized routing (not just tier-based)
# ---------------------------------------------------------------------------
# Based on empirical testing (empirical_labeling.py):
#
#   minimax-m3 passes: factual, math, sentiment, summarize, ner (5/8)
#   kimi-k2p7-code passes: logic, code_gen (+ all of minimax's) (7/8)
#   minimax-m3 returns empty on code_debug and logic (thinking exhaustion)
#
# Token comparison per task:
#   minimax-m3 has ~150-220 prompt token overhead (different tokenizer)
#   kimi-k2p7-code has ~21-120 prompt tokens (much cheaper per call)
#   kimi WINS on tokens for 7/8 tasks, minimax only wins on NER (343 vs 397)
#
# Optimal strategy:
#   - For tasks minimax CAN do: still use kimi if it uses fewer tokens
#   - Only use minimax for NER (only category where it's cheaper tokens)
#   - Always use kimi for logic/code (minimax returns empty content)
#   - Gemma models (when available) should handle mid-tier for even cheaper

# Empirical routing: category → preferred model pattern (matched against ALLOWED_MODELS)
# "kimi" = prefer kimi-k2p7-code (token-efficient, reliable)
# "gemma" = prefer gemma models (mid-tier, potentially cheaper when available)
# "minimax" = prefer minimax-m3 (only for NER where it had fewer tokens)
# "any" = use cheapest available

CATEGORY_ROUTING = {
    "factual":     "kimi",   # kimi: 256 tok vs minimax: 379 tok
    "math":        "kimi",   # kimi: 331 tok vs minimax: 614 tok
    "sentiment":   "kimi",   # kimi: 306 tok vs minimax: 415 tok
    "summarize":   "gemma",  # Try gemma first (mid-tier), fallback to kimi
    "ner":         "minimax", # minimax: 343 tok vs kimi: 397 tok (only category minimax wins)
    "logic":       "kimi",   # minimax returns empty content; kimi handles it
    "code_debug":  "kimi",   # minimax returns empty content; kimi handles it
    "code_gen":    "kimi",   # minimax fails code execution tests; kimi passes
}

# Category-specific max_tokens — empirically tuned per category
CATEGORY_MAX_TOKENS = {
    "sentiment":   200,   # "Sentiment: positive. One sentence justification."
    "factual":     600,   # Concise factual answer
    "summarize":   300,   # One sentence or short paragraph
    "ner":         400,   # JSON with entity lists
    "math":        800,   # Step-by-step + answer
    "logic":       3000,  # kimi-k2p7-code uses thinking tokens; needs high max_tokens
    "code_debug":  1000,  # Code + brief explanation
    "code_gen":    600,   # Function code
}


def select_model(category: str, allowed_models: list) -> str:
    """
    Select the best model for this category based on empirical routing data.
    
    Priority order depends on category:
      - "kimi" categories: look for kimi first, then gemma, then minimax, then any
      - "gemma" categories: look for gemma first, then kimi, then minimax, then any  
      - "minimax" categories: look for minimax first, then gemma, then kimi, then any
    
    Falls back to tier-based estimation for unknown models.
    """
    preference = CATEGORY_ROUTING.get(category, "kimi")
    
    # Define search patterns for each preference
    patterns = {
        "kimi":   ["kimi", "k2p7", "k2p6"],
        "gemma":  ["gemma", "gemma-4-31b", "gemma-4-26b"],
        "minimax": ["minimax", "m3", "mini"],
    }
    
    # Build preference order: [preferred, gemma, kimi, minimax] (deduplicated)
    search_order = []
    seen = set()
    for pref in [preference, "gemma", "kimi", "minimax"]:
        if pref not in seen:
            search_order.append(pref)
            seen.add(pref)
    
    # Search for models matching each preference
    for pref in search_order:
        pats = patterns.get(pref, [])
        for pat in pats:
            for model in allowed_models:
                if pat in model.lower():
                    log.info(f"Category '{category}' (pref={preference}) -> model '{model}'")
                    return model
    
    # Fallback: pick first available model
    if allowed_models:
        selected = allowed_models[0]
        log.warning(f"Category '{category}' -> fallback model '{selected}' (no preference match)")
        return selected
    
    raise ValueError(f"No allowed models available! ALLOWED_MODELS={allowed_models}")
    log.info(f"Category '{category}' (tier {min_tier}) -> model '{selected}' (tier {sufficient[0][1]})")
    return selected


def get_most_reliable_model(allowed_models: list) -> str:
    """
    Return the most reliable model for fallback.
    Empirically: kimi-k2p7-code is most reliable (handles all task types).
    Falls back to any available model.
    """
    if not allowed_models:
        raise ValueError("No allowed models available for fallback!")
    # Prefer kimi, then gemma, then minimax, then first available
    for pat in ["kimi", "k2p7", "k2p6"]:
        for m in allowed_models:
            if pat in m.lower():
                return m
    for pat in ["gemma"]:
        for m in allowed_models:
            if pat in m.lower():
                return m
    return allowed_models[0]


# ---------------------------------------------------------------------------
# 3. MINIMAL CATEGORY-SPECIFIC PROMPTS — token-optimized
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS = {
    "sentiment": "Classify the sentiment as positive, negative, or neutral. Provide a one-sentence justification.",

    "factual": "Answer the question accurately and concisely. Output only the answer, no preamble.",

    "summarize": "Summarize the text as requested. Follow the format/length constraint exactly. Output only the summary.",

    "ner": "Extract named entities from the text. Return a JSON object with keys: persons, organizations, locations, dates. Include only entities explicitly mentioned in the text.",

    "math": "Solve the problem. Show brief steps, then end with 'Answer: [result]'. Keep it concise.",

    "logic": "Solve the logic puzzle. State the constraints, derive the solution concisely, and end with 'Answer: [result]'. Do not include internal deliberation or self-doubt.",

    "code_debug": "Identify the bug in the code. Output the corrected code in a code block, then explain the fix in one sentence. Do not show your analysis process.",

    "code_gen": "Write the requested code. Return only the code in a code block with minimal explanation.",
}


def get_system_prompt(category: str) -> str:
    return SYSTEM_PROMPTS.get(category, "Answer accurately and concisely.")


def get_max_tokens(category: str) -> int:
    return CATEGORY_MAX_TOKENS.get(category, 1024)


# ---------------------------------------------------------------------------
# 3b. STRUCTURED OUTPUT — response_format for JSON-based categories
# Uses Fireworks' JSON mode to guarantee valid JSON output and save tokens
# (no markdown code fences, no format-parsing overhead)
# ---------------------------------------------------------------------------

# NER: force JSON object with entity arrays
NER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "persons":          {"type": "array", "items": {"type": "string"}},
        "organizations":    {"type": "array", "items": {"type": "string"}},
        "locations":        {"type": "array", "items": {"type": "string"}},
        "dates":            {"type": "array", "items": {"type": "string"}},
    },
    "required": ["persons", "organizations", "locations", "dates"],
}

# Sentiment: force JSON object with label + justification
SENTIMENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "sentiment":    {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "justification": {"type": "string"},
    },
    "required": ["sentiment", "justification"],
}

# Category → response_format dict (only for categories that benefit from structured output)
CATEGORY_RESPONSE_FORMAT = {
    "ner":       {"type": "json_object", "schema": NER_JSON_SCHEMA},
    "sentiment": {"type": "json_object", "schema": SENTIMENT_JSON_SCHEMA},
}


def get_response_format(category: str) -> Optional[dict]:
    """Return response_format dict for categories that use structured output, else None."""
    return CATEGORY_RESPONSE_FORMAT.get(category)


def format_response(category: str, answer: str) -> str:
    """
    Post-process the model's response based on category.
    For sentiment JSON output, convert back to the expected text format:
      "Sentiment: positive. <justification>"
    For NER, ensure the JSON string is clean (strip markdown fences if present).
    """
    if category == "sentiment":
        # Model returned JSON like {"sentiment": "positive", "justification": "..."}
        # Convert to text format that LLM-Judge expects
        try:
            data = json.loads(answer)
            sentiment = data.get("sentiment", "unknown")
            justification = data.get("justification", "")
            return f"Sentiment: {sentiment}. {justification}"
        except (json.JSONDecodeError, TypeError):
            # If JSON parsing fails, return as-is (model may have returned text)
            return answer

    elif category == "ner":
        # Strip markdown code fences if present (fallback for models that ignore response_format)
        stripped = answer.strip()
        if stripped.startswith("```"):
            # Remove ```json ... ``` wrapper
            lines = stripped.split("\n")
            # Remove first line (```json or ```) and last line (```)
            inner_lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            stripped = "\n".join(inner_lines).strip()
        # Validate JSON
        try:
            data = json.loads(stripped)
            # Return compact JSON string
            return json.dumps(data, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return answer

    return answer


# ---------------------------------------------------------------------------
# 4. FIREWORKS API CALL — single completion per task
# ---------------------------------------------------------------------------

def call_fireworks(task_id: str, prompt: str, model: str, system_prompt: str,
                   category: str, max_tokens: int) -> str:
    """
    Make a single API call to Fireworks AI via the OpenAI-compatible endpoint.
    Returns the model's answer text.
    Handles None content (thinking models that exhaust tokens) with fallback.
    Passes response_format for categories that use structured JSON output.
    """
    response_format = get_response_format(category)

    # Build kwargs — only include response_format when set (some models reject it)
    api_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }
    if response_format:
        api_kwargs["response_format"] = response_format

    try:
        response = client.chat.completions.create(**api_kwargs)
        answer = response.choices[0].message.content
        usage = response.usage

        # Handle None content — model exhausted tokens on internal reasoning
        if answer is None or answer.strip() == "":
            log.warning(f"Task {task_id} model '{model}' returned empty content "
                        f"({usage.total_tokens} tokens used, likely thinking exhaustion)")
            # Retry with most reliable model and higher max_tokens
            fallback = get_most_reliable_model(ALLOWED_MODELS)
            if fallback != model:
                log.info(f"Task {task_id} retrying with reliable model: {fallback}")
                # On fallback, drop response_format — some models don't support it
                fallback_kwargs = {
                    "model": fallback,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": max(max_tokens, 1024),
                }
                response2 = client.chat.completions.create(**fallback_kwargs)
                answer2 = response2.choices[0].message.content
                if answer2 and answer2.strip():
                    log.info(f"Task {task_id} fallback succeeded ({response2.usage.total_tokens} tokens)")
                    return format_response(category, answer2.strip())
            # If fallback also returns None, return error
            return "[Error: model returned empty content]"

        answer = answer.strip()
        log.info(f"Task {task_id} [{category}] model='{model}' "
                 f"({usage.total_tokens} tokens, {usage.completion_tokens} completion)")
        return format_response(category, answer)

    except Exception as e:
        log.error(f"Task {task_id} API call failed: {e}")
        # Try fallback with a different model — drop response_format for compatibility
        fallback_models = [m for m in ALLOWED_MODELS if m != model]
        if fallback_models:
            # Pick the most reliable for fallback
            fallback = get_most_reliable_model(fallback_models)
            log.warning(f"Task {task_id} retrying with fallback model: {fallback}")
            try:
                fallback_kwargs = {
                    "model": fallback,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": max(max_tokens, 1024),
                }
                response = client.chat.completions.create(**fallback_kwargs)
                answer = response.choices[0].message.content
                if answer and answer.strip():
                    log.info(f"Task {task_id} fallback succeeded ({response.usage.total_tokens} tokens)")
                    return format_response(category, answer.strip())
                return "[Error: fallback also returned empty content]"
            except Exception as e2:
                log.error(f"Task {task_id} fallback also failed: {e2}")

        return f"[Error: {str(e)}]"


# ---------------------------------------------------------------------------
# 5. MAIN — read tasks, process, write results
# ---------------------------------------------------------------------------

def main():
    if not ALLOWED_MODELS:
        log.error("ALLOWED_MODELS environment variable is empty or not set!")
        sys.exit(1)

    if not API_KEY or not BASE_URL:
        log.error("FIREWORKS_API_KEY or FIREWORKS_BASE_URL not set!")
        sys.exit(1)

    log.info(f"Allowed models: {ALLOWED_MODELS}")
    log.info(f"Reading tasks from: {INPUT_PATH}")

    # Read input tasks
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    log.info(f"Loaded {len(tasks)} tasks")

    results = []
    total_tokens = 0

    for task in tasks:
        task_id = task.get("task_id", "unknown")
        prompt = task.get("prompt", "")

        # Step 1: Classify the task
        category = classify_task(prompt)
        log.info(f"Task {task_id} classified as: {category}")

        # Step 2: Select cheapest sufficient model
        model = select_model(category, ALLOWED_MODELS)

        # Step 3: Get minimal system prompt + max_tokens
        system_prompt = get_system_prompt(category)
        max_tokens = get_max_tokens(category)

        # Step 4: Call Fireworks API
        answer = call_fireworks(task_id, prompt, model, system_prompt, category, max_tokens)

        # Step 5: Store result
        results.append({
            "task_id": task_id,
            "answer": answer
        })

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log.info(f"Results written to {OUTPUT_PATH} ({len(results)} tasks)")
    log.info("Done.")


if __name__ == "__main__":
    main()
