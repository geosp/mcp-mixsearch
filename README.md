# MCP MixSearch

A comprehensive Model Context Protocol (MCP) server for advanced web search functionality with multi-engine support and intelligent backend selection.

## Features

- **Multi-Engine Search**: Access to multiple search engines (Brave, DuckDuckGo, Google, Bing, Yandex) via DDGS library
- **Advanced Filtering**: Time-based, geographic, language, and content type filtering
- **Intelligent Backend Selection**: Automatically chooses optimal search engine based on parameters
- **Full Content Extraction**: Extract readable content from search results and specific URLs
- **Dual Interface**: Both MCP protocol and REST API with identical functionality
- **Graceful Fallbacks**: Browser-based search for reliability when APIs fail

## Quick Start

### Install and Run

```bash
# Install
uv sync

# Run in MCP stdio mode (default)
uv run mcp-mixsearch

# Run in MCP HTTP mode
uv run mcp-mixsearch --mode mcp

# Or run with REST API
uv run mcp-mixsearch --mode rest
```

### Use as a Dependency

See [Using as Dependency](USING_AS_DEPENDENCY.md) for creating your own MCP servers.

## Configuration

Set environment variables in a `.env` file or export them:

```env
# Server Configuration
MCP_HOST=localhost
MCP_PORT=3000
MCP_TRANSPORT=stdio  # or 'http'
MCP_AUTH_ENABLED=true
MCP_CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

# Web Search Configuration
BRAVE_API_KEY=your_brave_api_key_here
MAX_CONTENT_LENGTH=500000
MAX_CONCURRENT_REQUESTS=5

# Logging
LOG_LEVEL=INFO
```

## Running Modes

mcp-mixsearch supports three distinct running modes:

### 1. MCP HTTP Mode
Runs MCP server over HTTP without REST API endpoints.

```bash
uv run mcp-mixsearch --mode mcp
```

### 2. MCP Stdio Mode (Default)
Runs MCP server over stdio without REST API endpoints.

```bash
uv run mcp-mixsearch --mode stdio
# Or just run without flags (default)
uv run mcp-mixsearch
```

### 3. REST API + MCP Mode
Runs both REST API endpoints and MCP protocol over HTTP.

```bash
uv run mcp-mixsearch --mode rest
```

### Environment Variables

You can also control modes using environment variables:

```bash
# MCP over HTTP
MCP_TRANSPORT=http MCP_ONLY=true uv run mcp-mixsearch

# MCP over stdio
MCP_TRANSPORT=stdio MCP_ONLY=true uv run mcp-mixsearch

# REST API + MCP over HTTP
MCP_TRANSPORT=http MCP_ONLY=false uv run mcp-mixsearch
```

In HTTP modes, the server runs on `http://localhost:3000` with:
- MCP endpoint: `http://localhost:3000/mcp`
- REST API docs: `http://localhost:3000/docs` (when REST API enabled)
- Health check: `http://localhost:3000/health` (when REST API enabled)

## Available Tools

### MCP Tools
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

### REST API Endpoints
- `GET /search/full_web_search` - Same as `full_web_search` with identical parameters
- `GET /search/get_web_search_summaries` - Same as `get_web_search_summaries` with identical parameters
- `GET /search/get_single_web_page_content` - Same as `get_single_web_page_content`

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
```bash
# MCP
{"query": "AI developments", "limit": 5}

# REST
GET /search/get_web_search_summaries?query=AI%20developments&limit=5
```

**Advanced filtering:**
```bash
# MCP
{"query": "climate policy", "country": "FR", "language": "fr", "recency_days": 30, "source": "news"}

# REST
GET /search/get_web_search_summaries?query=climate%20policy&country=FR&language=fr&recency_days=30&source=news
```

## Project Structure

```
mcp-mixsearch/
├── features/             # Feature implementations
│   └── web_search/       # Web search feature
│       ├── __init__.py
│       ├── models.py     # Pydantic models
│       ├── service.py    # Multi-engine search logic
│       ├── tool.py       # MCP tool registrations
│       ├── routes.py     # REST API routes
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

- **mcp-weather**: Core MCP infrastructure
- fastmcp: MCP protocol implementation
- httpx: HTTP client for content extraction
- playwright: Browser automation for dynamic content
- beautifulsoup4: HTML parsing
- fake-useragent: Random user agents

## License

See LICENSE file.