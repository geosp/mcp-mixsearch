# MCP MixSearch

A comprehensive Model Context Protocol (MCP) server for advanced web search functionality with multi-engine support and intelligent backend selection.

## Features

- **Multi-Engine Search**: The official Brave Search API (with a key) and the DDGS metasearch library, with browser-scraping fallbacks
- **Advanced Filtering**: Time-based, geographic, language, and content type filtering
- **Full Content Extraction**: Main-content extraction with [trafilatura](https://trafilatura.readthedocs.io), rendering JavaScript pages in a shared headless Firefox when needed
- **Safe Fetching**: Only public http(s) URLs are fetched (see [Security](#security))
- **Two Transports**: MCP over stdio or streamable HTTP, built on [mcp-service-kit](https://github.com/geosp/mcp-service-kit)
- **Graceful Fallbacks**: Browser-based search for reliability when APIs fail

## Quick Start

### Install and Run

```bash
# Install
uv sync

# Run in MCP stdio mode (default)
uv run mcp-mixsearch

# Run in MCP HTTP mode (local use: no auth)
uv run mcp-mixsearch --mode http --no-auth
```

## Configuration

Set environment variables in a `.env` file or export them. CLI flags take precedence over `.env`.

```env
# Server Configuration (mcp-service-kit)
MCP_TRANSPORT=stdio     # or 'http'  (--mode)
MCP_HOST=0.0.0.0        # (--host)
MCP_PORT=3000           # (--port)
MCP_AUTH_ENABLED=false  # (--no-auth)

# Web Search Configuration
BRAVE_API_KEY=your_brave_api_key_here  # optional: enables the Brave Search API engine
MAX_CONTENT_LENGTH=500000              # default per-page content limit (characters)
MAX_CONCURRENT_REQUESTS=5              # concurrent page extractions
DDGS_BACKEND=auto                      # ddgs backend(s), e.g. auto or duckduckgo,bing
ALLOW_PRIVATE_URLS=false               # true allows private/loopback URLs (trusted networks only)
```

## Running Modes

### MCP Stdio Mode (Default)

```bash
uv run mcp-mixsearch --mode stdio
# Or just run without flags
uv run mcp-mixsearch
```

### MCP HTTP Mode

```bash
uv run mcp-mixsearch --mode http --port 3000 --no-auth
# Or via the environment
MCP_TRANSPORT=http MCP_AUTH_ENABLED=false uv run mcp-mixsearch
```

The server has no auth provider, so HTTP mode needs `--no-auth` (`MCP_AUTH_ENABLED=false`);
without it the server refuses to start. Put an authenticating gateway in front of it if it is
reachable by others.

In HTTP mode the server runs on `http://localhost:3000` with:
- MCP endpoint: `http://localhost:3000/mcp`
- Health check: `http://localhost:3000/health`

Run `uv run mcp-mixsearch --help` for all options, including `--log-level`.

## Available Tools

1. **full_web_search**
   - Comprehensive web search with content extraction
   - Multi-engine search with intelligent backend selection
   - **Advanced filtering**: time, language, geographic, content type filters
   - Args: query, limit (1-10), include_content, max_content_length, top_n, recency_days, source, language, country

2. **get_web_search_summaries**
   - Lightweight search returning only summaries
   - Same advanced filtering capabilities as full_web_search
   - Args: query, limit (1-10), top_n, recency_days, source, language, country

3. **get_single_web_page_content**
   - Extract content from a specific URL
   - Args: url, max_content_length

## Advanced Search Features

### Multi-Engine Architecture
Engines are tried in order. The first result set whose titles and descriptions match the query
well enough is used; if none does, the best one found is returned.

1. **Brave Search API**: only when `BRAVE_API_KEY` is set (web and news)
2. **DDGS**: metasearch library, `backend` from `DDGS_BACKEND` (`auto` by default)
3. **Brave (browser)**: scrapes search.brave.com in headless Firefox
4. **DuckDuckGo (HTML)**: scrapes the DuckDuckGo HTML results page

Page content is fetched over HTTP and extracted with trafilatura. Pages that need JavaScript
or return a bot check are rendered in one shared headless Firefox, with a new browser context
per page.

### Supported Parameters
- **Core**: `query` (required), `limit`/`top_n`, `include_content`, `max_content_length`
- **Time filtering**: `recency_days` (1=day, 7=week, 30=month, 365=year)
- **Content type**: `source` ("news", "images", "videos", "web")
- **Language filtering**: `language` (e.g., "en", "es", "fr", "de"). Applied directly by the Brave
  Search API; for the other engines it refines `country` into a region such as `ca-fr`
- **Geographic filtering**: `country` (e.g., "US", "GB", "FR", "DE")

## Security

The extraction tools fetch URLs chosen by the model, so they only fetch **public http(s)
URLs**. `file://` and other schemes are rejected, and so are hosts that resolve to loopback,
private, link-local (including cloud metadata such as `169.254.169.254`) or other non-public
addresses. The check runs before the fetch, on every HTTP redirect, and on every request the
browser makes. Set `ALLOW_PRIVATE_URLS=true` only on trusted networks where fetching internal
sites is intended.

Known limitation: DNS rebinding (a host that resolves to a public address when checked and a
private one when connected) is not prevented.

### Usage Examples

**Basic search:**
```json
{"query": "AI developments", "limit": 5}
```

**Advanced filtering:**
```json
{"query": "climate policy", "country": "FR", "language": "fr", "recency_days": 30, "source": "news"}
```

## Project Structure

```
mcp-mixsearch/
├── features/             # Feature implementations
│   └── web_search/       # Web search feature
│       ├── __init__.py
│       ├── service.py    # Orchestrates engines and content extraction
│       ├── engines.py    # Brave API, DDGS, Brave and DuckDuckGo scraping engines
│       ├── extraction.py # HTTP + trafilatura extraction with browser fallback
│       ├── browser.py    # Shared headless Firefox
│       ├── filters.py    # Normalized search filters and per-engine parameters
│       ├── url_safety.py # Public http(s) URL guard
│       ├── models.py     # SearchResult
│       ├── tool.py       # MCP tool registrations
│       ├── instructions.md          # Full web search documentation
│       ├── instructions_summaries.md # Search summaries documentation
│       └── instructions_single_page.md # Single page extraction documentation
├── tests/                # pytest suite (offline by default)
├── config.py             # Configuration management
├── server.py             # Main server entry point
├── pyproject.toml        # Project configuration
├── uv.lock              # Dependency lock file
├── README.md
└── LICENSE
```

## Development

### Testing

```bash
uv run pytest          # offline tests: network, DNS and the browser are faked
uv run pytest -m live  # live tests against real search engines and websites
uv run ruff check
```

Browser-based paths need Firefox for Playwright: `uv run playwright install firefox`.
CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs ruff and the offline tests on
pull requests and pushes to `main`.

### Building

```bash
uv build
```

## Dependencies

- **mcp-service-kit**: MCP server infrastructure (transports, CLI, config)
- fastmcp: MCP protocol implementation
- ddgs: Metasearch library
- httpx: HTTP client for search APIs and content extraction
- trafilatura: Main-content extraction
- playwright: Browser automation for dynamic content (pinned to match the Docker image's Firefox)
- beautifulsoup4: HTML parsing
- fake-useragent: Random user agents

## License

See LICENSE file.