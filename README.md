# MCP MixSearch

A comprehensive Model Context Protocol (MCP) server for advanced web search functionality that merges results from several search engines.

## Features

- **Multi-Engine Search**: Queries the official Brave Search API (with a key), the DDGS metasearch library and DuckDuckGo in parallel and merges their results, with a browser-scraping fallback
- **Advanced Filtering**: Time-based, geographic, language, and content type filtering
- **Full Content Extraction**: Main-content extraction with [trafilatura](https://trafilatura.readthedocs.io), rendering JavaScript pages in a shared headless Firefox when needed
- **Safe Fetching**: Only public http(s) URLs are fetched (see [Security](#security))
- **Two Transports**: MCP over stdio or streamable HTTP, built on [mcp-service-kit](https://github.com/geosp/mcp-service-kit)
- **Graceful Fallbacks**: A failing or slow engine is skipped; browser-based search fills in when too few results come back

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
ENGINE_TIMEOUT_SECONDS=10              # per-engine timeout for the engines queried in parallel
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
   - Results merged from several engines, each listing the engines that returned it
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
The cheap engines are queried in parallel, each with its own timeout (`ENGINE_TIMEOUT_SECONDS`,
10 s by default). An engine that fails or times out is logged and skipped:

- **Brave Search API** (`BraveAPI`): only when `BRAVE_API_KEY` is set (web and news)
- **DDGS**: metasearch library, `backend` from `DDGS_BACKEND` (`auto` by default)
- **DuckDuckGo (HTML)** (`DuckDuckGo`): scrapes the DuckDuckGo HTML results page (web only)

Their ranked lists are merged with reciprocal rank fusion: a result scores `1 / (60 + rank)` for
each engine that lists it, so results that several engines rank highly come first. Duplicates are
merged by normalized URL (case, `www.`, tracking parameters such as `utm_*`, fragments and
trailing slashes are ignored), and each result lists the engines that returned it, for example
`Engines: BraveAPI, DDGS`.

When fewer results than `limit` come back for a web search, **Brave (browser)** (`Brave`) scrapes
search.brave.com in headless Firefox as a fallback, with a 30 s timeout, and its results are
merged in.

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
│       ├── fusion.py     # URL normalization and reciprocal rank fusion
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