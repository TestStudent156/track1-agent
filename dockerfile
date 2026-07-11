# AMD Developer Hackathon ACT II — Track 1
# Hybrid Token-Efficient Routing Agent
# Docker image: linux/amd64 required by judging VM

FROM python:3.12-slim

# Metadata
LABEL maintainer="Hackathon Team"
LABEL description="Track 1: Hybrid Token-Efficient Routing Agent"
LABEL track="1"
LABEL version="1.0"

# Set working directory
WORKDIR /app

# Install only what we need (keeps image small — must be < 10GB)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create I/O directories (harness will mount /input and /output,
# but we create them as fallback for local testing)
RUN mkdir -p /input /output

# Set environment defaults (harness will override at runtime)
ENV INPUT_PATH=/input/tasks.json
ENV OUTPUT_PATH=/output/results.json

# Run the agent
ENTRYPOINT ["/app/entrypoint.sh"]
