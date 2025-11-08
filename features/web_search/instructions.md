Get comprehensive web search results with full page content extraction.

Use this when you need detailed content from web sources for comprehensive research and analysis. This searches the web and extracts the full content from each result page.

Use this for comprehensive research or detailed information from web sources.

Args:
    query: Search query string (1-200 characters)
    limit: Number of results to return with full content (1-10, default 5)
    include_content: Whether to extract full page content (default true)
    max_content_length: Maximum characters per result content (0 = no limit)
    top_n: Alternative name for limit (for compatibility)
    recency_days: Days to look back for recent content (time filtering)
    source: Content type filter ("news", "images", "videos", etc.)
    language: Language filter (e.g., "en", "es", "fr", "de")
    country: Geographic filter (e.g., "US", "GB", "FR", "DE")

Returns:
    Formatted text containing search results with full extracted content

## Parameter Usage Guidelines

### query (required)
- Search query string (1-200 characters)
- Use specific, descriptive search terms

### limit (optional, default 5)
- Range: 1-10 results
- Higher limits take longer due to content extraction

### include_content (optional, default true)
- Set to `true` for full content extraction (default)
- Set to `false` to get only titles, URLs, and descriptions

### max_content_length (optional, default unlimited)
- Limits characters per result to manage response size
- Common values: `10000` (focused content), `50000` (detailed research), `null` (no limit)

### top_n (optional, compatibility parameter)
- Alternative name for `limit` parameter
- Range: 1-10 results

### recency_days (optional, time filtering)
- Filters results to recent content only
- Common values: `1` (past day), `7` (past week), `30` (past month), `365` (past year)
- Use `-1` or `null` for no time filter

### source (optional, content type filtering)
- Filters by content type
- Supported values:
  - `"news"`: News articles and current events
  - `"images"`: Image search results
  - `"videos"`: Video content
  - `"web"` or null: Regular web search (default)

### language (optional, language filtering) 
- Filters results by language
- Supported values: Language codes like `"en"`, `"es"`, `"fr"`, `"de"`, `"zh"`

### country (optional, geographic filtering)
- Filters results by geographic region/country
- Supported values: Country codes like `"US"`, `"GB"`, `"FR"`, `"DE"`, `"CA"`

## Usage Examples

### Basic search with default settings:
```json
{
  "query": "sustainable energy solutions 2024"
}
```

### Quick overview (smaller limit):
```json
{
  "query": "latest AI developments",
  "limit": 3
}
```

### Recent news search with time filtering:
```json
{
  "query": "AI technology breakthroughs",
  "source": "news",
  "recency_days": 7,
  "language": "en"
}
```

### Geographic and language filtering:
```json
{
  "query": "climate change policy",
  "country": "FR",
  "language": "fr",
  "limit": 5
}
```

### Comprehensive research with all parameters:
```json
{
  "query": "machine learning frameworks comparison",
  "limit": 8,
  "include_content": true,
  "max_content_length": 25000,
  "recency_days": 30,
  "language": "en"
}
```

### Content type specific search:
```json
{
  "query": "python tutorial",
  "source": "videos",
  "limit": 5,
  "include_content": false
}
```

### Source identification only:
```json
{
  "query": "quantum computing breakthroughs",
  "limit": 5,
  "include_content": false
}
```

## When to Use This
- Use when you need detailed content from multiple sources
- Use for comprehensive research on complex topics
- Use when analyzing and comparing information across sources
- Use for gathering supporting evidence or documentation
- Use when you need the full context from web pages

## Related Functionality
- For quick topic exploration without content, use the search summaries functionality
- When you have a specific URL to extract, use the single page content extraction functionality