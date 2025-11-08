Get lightweight web search results with only result summaries.

Use this when you need a quick overview of available sources without full content. This gets search result titles, URLs, and descriptions for quick research or when you only need an overview of available information.

Use this when you want to quickly understand what information is available on a topic before diving deeper with full content extraction.

Args:
    query: Search query string (1-200 characters)
    limit: Number of search result summaries to return (1-10, default 5)
    top_n: Alternative name for limit (for compatibility)
    recency_days: Days to look back for recent content (time filtering)
    source: Content type filter ("news", "images", "videos", etc.)
    language: Language filter (e.g., "en", "es", "fr", "de")
    country: Geographic filter (e.g., "US", "GB", "FR", "DE")

Returns:
    Formatted text containing search result summaries (title, URL, description)

## Parameter Usage Guidelines

### query (required)
- Search query string (1-200 characters)
- Use specific, descriptive search terms

### limit (optional, default 5)
- Range: 1-10 results

## Usage Examples

### Basic topic exploration:
```json
{
  "query": "artificial intelligence ethics"
}
```

### Quick source discovery:
```json
{
  "query": "kubernetes security best practices",
  "limit": 3
}
```

### Recent news exploration:
```json
{
  "query": "AI developments",
  "source": "news",
  "recency_days": 7,
  "language": "en"
}
```

### Geographic research:
```json
{
  "query": "renewable energy policies",
  "country": "DE",
  "language": "en",
  "limit": 8
}
```

### Content type discovery:
```json
{
  "query": "machine learning tutorials",
  "source": "videos",
  "limit": 5
}
```

### Complete parameter example:
```json
{
  "query": "climate change adaptation strategies",
  "limit": 6,
  "recency_days": 30,
  "language": "en",
  "country": "US"
}
```

## When to Choose This Tool

### Primary Decision Criteria:
- **Choose this for initial research phase**: Understand what sources are available
- **Choose this for topic exploration**: Get an overview before deep diving
- **Choose this for source identification**: Find relevant URLs for later extraction
- **Choose this for quick fact-checking**: Verify if information sources exist
- **Choose this for research planning**: Identify the scope of available information

## Decision Matrix: When to Use Each Tool

### Use `get_web_search_summaries` when:
- ✅ You need to explore what's available on a topic
- ✅ You want to identify relevant sources quickly
- ✅ You're doing preliminary research
- ✅ You need to validate if sources exist
- ✅ You want to see search result diversity
- ✅ Speed is more important than content depth

### Use `full_web_search` when:
- ✅ You need actual content from sources
- ✅ You're doing detailed research or analysis
- ✅ You need to cite or reference specific information
- ✅ You want to compare information across sources
- ✅ Content depth is more important than speed

### Use `get_single_web_page_content` when:
- ✅ You have specific URLs to extract
- ✅ You found relevant URLs from summaries
- ✅ You need to extract from known sources

## Workflow Patterns

### Two-stage research:
1. Use `get_web_search_summaries` to identify sources
2. Use `get_single_web_page_content` on promising URLs
3. Or use `full_web_search` with focused query

### Topic mapping:
1. Use `get_web_search_summaries` with broad terms
2. Analyze result diversity and topics
3. Use `full_web_search` for detailed investigation

### Source validation:
1. Use `get_web_search_summaries` to check if sources exist
2. Evaluate source quality and relevance
3. Proceed with content extraction if validated