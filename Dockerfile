FROM python:3.11-slim

# Install system dependencies (git + build tools for Python packages)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (universal package runner for MCP)
RUN pip install --no-cache-dir uv

# Expose the default MCP port (used by most servers)
EXPOSE 3000

# Default entrypoint lets you pass in `uvx` args via Kubernetes or docker run
ENTRYPOINT ["uvx"]