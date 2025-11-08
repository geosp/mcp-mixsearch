Extract and return the full content from a single web page URL.

Use this when you have a specific URL and need the full text content for analysis or reference.

Args:
    url: The URL of the web page to extract content from
    max_content_length: Maximum characters for the extracted content (0 = no limit)

Returns:
    Formatted text containing the extracted page content with word count

## Parameter Usage Guidelines

### url (required)
- Must be a valid HTTP or HTTPS URL
- Include the full URL with protocol (http:// or https://)
- Examples: 
  - "https://example.com/article"
  - "https://docs.python.org/3/library/asyncio.html"
  - "https://github.com/user/repo/blob/main/README.md"

### max_content_length (optional, default unlimited)
- Limits the extracted content to specified character count
- Common values: `10000` (summaries), `50000` (full pages), `null` (no limit)

## Usage Examples

### Basic content extraction:
```json
{
  "url": "https://example.com/blog/ai-trends-2024"
}
```

### Extract with content limit:
```json
{
  "url": "https://docs.example.com/api-reference",
  "max_content_length": 20000
}
```

### Extract documentation:
```json
{
  "url": "https://github.com/project/docs/installation.md",
  "max_content_length": 10000
}
```

### Extract complete article:
```json
{
  "url": "https://techblog.com/comprehensive-guide"
}
```

### Complete parameter example:
```json
{
  "url": "https://docs.python.org/3/library/asyncio.html",
  "max_content_length": 50000
}
```

## When to Choose This Tool
- Choose this when you have a specific URL from search results or references
- Choose this for extracting content from documentation, articles, or blog posts
- Choose this when you need to analyze or reference specific webpage content
- Choose this for following up on URLs found in search results
- Choose this when extracting content from GitHub README files or documentation

## Error Handling
- If URL is inaccessible, an error message will be provided
- Some sites may block automated access - try alternative URLs
- Dynamic content may require multiple attempts
- Large pages may timeout - use content length limits

## Alternative Tools
- Use `full_web_search` when you need to find relevant pages first
- Use `get_web_search_summaries` for discovering URLs to extract