# MCP MixSearch

A comprehensive Model Context Protocol (MCP) server for advanced web search functionality with multi-engine support and intelligent backend selection.

## Features

- **Multi-Engine Search**: Access to multiple search engines (Brave, DuckDuckGo, Google, Bing, Yandex) via DDGS library
- **Advanced Filtering**: Time-based, geographic, language, and content type filtering
- **Intelligent Backend Selection**: Automatically chooses optimal search engine based on parameters
- **Full Content Extraction**: Extract readable content from search results and specific URLs
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
BRAVE_API_KEY=your_brave_api_key_here
MAX_CONTENT_LENGTH=500000
MAX_CONCURRENT_REQUESTS=5
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
- **Primary**: DDGS library with multiple backend support (Brave, DuckDuckGo, Google, Bing, Yandex)
- **Intelligent backend selection**: Automatically chooses best engine based on parameters
- **Fallbacks**: Browser-based search for reliability

### Supported Parameters
- **Core**: `query` (required), `limit`/`top_n`, `include_content`, `max_content_length`
- **Time filtering**: `recency_days` (1=day, 7=week, 30=month, 365=year)
- **Content type**: `source` ("news", "images", "videos", "web")
- **Language filtering**: `language` (e.g., "en", "es", "fr", "de")
- **Geographic filtering**: `country` (e.g., "US", "GB", "FR", "DE")

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
│       ├── service.py    # Multi-engine search logic
│       ├── tool.py       # MCP tool registrations
│       ├── instructions.md          # Full web search documentation
│       ├── instructions_summaries.md # Search summaries documentation
│       └── instructions_single_page.md # Single page extraction documentation
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
pytest
```

### Building

```bash
uv build
```

## Dependencies

- **mcp-service-kit**: MCP server infrastructure (transports, CLI, config)
- fastmcp: MCP protocol implementation
- httpx: HTTP client for content extraction
- playwright: Browser automation for dynamic content
- beautifulsoup4: HTML parsing
- fake-useragent: Random user agents

## License

See LICENSE file.