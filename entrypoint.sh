#!/bin/bash
# Entrypoint for Track 1 Routing Agent
# Runs agent.py which reads /input/tasks.json and writes /output/results.json

set -e

echo "=== AMD Hackathon Track 1 — Token-Efficient Routing Agent ==="
echo "Input:  ${INPUT_PATH:-/input/tasks.json}"
echo "Output: ${OUTPUT_PATH:-/output/results.json}"
echo "Allowed models: ${ALLOWED_MODELS:-<not set>}"
echo "---"

# Run the agent
python3 /app/agent.py

# Exit with the agent's exit code
exit $?
