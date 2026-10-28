FROM python:3.14-slim

# Install system dependencies (git + build tools + Playwright dependencies)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        curl \
        build-essential \
        wget \
        gnupg \
        # Playwright browser dependencies
        libnss3 \
        libnspr4 \
        libatk-bridge2.0-0 \
        libdrm2 \
        libxkbcommon0 \
        libatspi2.0-0 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libxss1 \
        libasound2 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libcairo-gobject2 \
        libgtk-3-0 \
        libxfixes3 \
        libx11-xcb1 \
        libxcursor1 \
        libxi6 \
        # Fonts for better rendering
        fonts-liberation \
        fonts-noto-color-emoji \
        fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

# Install uv (universal package runner for MCP)
RUN pip install --no-cache-dir uv

# Set environment variables for Playwright (before installing, so browsers land in /ms-playwright)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true

# Pre-install Playwright and browsers to avoid runtime installation
# Keep the version in sync with the playwright pin in pyproject.toml
RUN pip install --no-cache-dir playwright==1.64.1 \
    && playwright install firefox \
    && playwright install-deps firefox

# Expose the default MCP port (used by most servers)
EXPOSE 3000

# Default entrypoint lets you pass in `uvx` args via Kubernetes or docker run
ENTRYPOINT ["uvx"]