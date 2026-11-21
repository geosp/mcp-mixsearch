FROM python:3.14-slim

# System packages: git (the mcp-service-kit dependency installs from a git tag at build time),
# build tools for any dependency without a wheel, and Playwright's browser libraries and fonts
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

# Keep in sync with UV_VERSION in .github/workflows/ci-gate.yml
RUN pip install --no-cache-dir uv==0.13.5

ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Dependencies only, from uv.lock: this layer and Firefox are reused until uv.lock changes
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Firefox from the locked playwright package, so the browser build always matches it
RUN /app/.venv/bin/playwright install --with-deps firefox \
    && rm -rf /var/lib/apt/lists/*

# The app itself: a tag runs exactly this code, with nothing downloaded at startup
COPY README.md LICENSE server.py config.py ./
COPY features ./features
RUN uv sync --locked --no-dev --no-editable

ENV PATH=/app/.venv/bin:$PATH \
    MCP_TRANSPORT=http

EXPOSE 3000

# Serves HTTP on port 3000 (MCP_TRANSPORT=http). Arguments are server options, for example
# `--port 3001`. The server has no auth provider: set MCP_AUTH_ENABLED=false to serve.
ENTRYPOINT ["mcp-mixsearch"]
