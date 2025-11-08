"""
Web Search Service

Provides web search functionality with multiple engines and content extraction.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, UTC
import urllib.parse
import httpx
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
import os
import json
from dotenv import load_dotenv
from ddgs import DDGS

# Load environment variables from .env file
load_dotenv()

# Configure logging to a file
logging.basicConfig(
    filename="web_search_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Ensure logging to file is properly configured
file_handler = logging.FileHandler("web_search_debug.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
    logger.addHandler(file_handler)

@dataclass
class SearchResult:
    title: str
    url: str
    description: str
    full_content: str = ""
    content_preview: str = ""
    word_count: int = 0
    timestamp: str = ""
    fetch_status: str = "success"
    error: Optional[str] = None

class WebSearchService:
    def __init__(self):
        self.ua = UserAgent()
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_content_length = 500000
        self.max_concurrent_requests = 5
        self.brave_api_key = os.getenv("BRAVE_API_KEY")

    async def search_and_extract(self, query: str, limit: int = 5,
                               max_content_length: Optional[int] = None,
                               include_content: bool = True, **kwargs) -> Dict[str, Any]:
        """Full web search with content extraction"""
        logger.info(f"Starting comprehensive web search for: '{query}' with parameters: {kwargs}")

        results = await self._multi_engine_search(query, limit, **kwargs)

        # Extract full content concurrently if requested
        if include_content:
            await self._extract_content_concurrent(results, max_content_length)

        return {
            "query": query,
            "results": [self._result_to_dict(r) for r in results],
            "total_results": len(results),
            "status": "success"
        }

    async def search_summaries(self, query: str, limit: int = 5, **kwargs) -> Dict[str, Any]:
        """Lightweight search returning only summaries using multi-engine approach"""
        logger.info(f"Starting multi-engine search for summaries: '{query}' with parameters: {kwargs}")

        # Use multi-engine search instead of just Brave API
        results = await self._multi_engine_search(query, limit, **kwargs)
        
        # Format results as summaries (no content extraction needed)
        return {
            "query": query,
            "results": [
                {
                    "title": r.title, 
                    "url": r.url, 
                    "description": r.description, 
                    "timestamp": r.timestamp
                } for r in results
            ],
            "total_results": len(results),
            "status": "success"
        }

    async def extract_single_page(self, url: str, max_content_length: Optional[int] = None) -> str:
        """Extract content from a single webpage"""
        logger.info(f"Extracting content from: {url}")

        return await self._extract_page_content(url, max_content_length)

    async def _multi_engine_search(self, query: str, limit: int, **kwargs) -> List[SearchResult]:
        """Try multiple search engines in order of preference"""
        engines = [
            ("DDGS", self._search_ddgs),  # DDGS with Brave/DDG backends (highest priority)
            ("Brave", self._search_brave),  # Browser-based Brave (fallback)
            ("DuckDuckGo", self._search_duckduckgo)  # Browser-based DDG (last resort)
        ]

        for engine_name, engine_func in engines:
            try:
                logger.info(f"Trying {engine_name} search engine")
                results = await engine_func(query, limit, **kwargs)
                if results and self._assess_result_quality(results, query) >= 0.3:
                    logger.info(f"Using results from {engine_name}: {len(results)} results")
                    return results[:limit]
            except Exception as e:
                logger.warning(f"Search engine {engine_name} failed: {e}")
                continue

        logger.warning("All search engines failed, returning empty results")
        return []

    async def _search_brave(self, query: str, limit: int, **kwargs) -> List[SearchResult]:
        """Browser-based Brave search"""
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=self.ua.random,
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()

                # Build search URL with parameters
                search_params = {'q': query, 'spellcheck': '1'}
                
                # Add country parameter if specified
                if kwargs.get('country'):
                    search_params['country'] = kwargs['country'].upper()
                    
                # Add language parameter if specified  
                if kwargs.get('language'):
                    search_params['lang'] = kwargs['language']
                
                # Add time filter if recency_days specified
                if kwargs.get('recency_days') is not None:
                    recency = kwargs['recency_days']
                    if recency == 1:
                        search_params['tf'] = 'd'  # past day
                    elif recency <= 7:
                        search_params['tf'] = 'w'  # past week 
                    elif recency <= 30:
                        search_params['tf'] = 'm'  # past month
                    elif recency <= 365:
                        search_params['tf'] = 'y'  # past year

                param_string = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in search_params.items()])
                search_url = f"https://search.brave.com/search?{param_string}"
                
                logger.info(f"Browser-based Brave search URL: {search_url}")
                await page.goto(search_url)
                await page.wait_for_load_state('networkidle')

                # Extract results
                results_data = await page.evaluate("""
                    () => {
                        const results = [];
                        document.querySelectorAll('.snippet').forEach(el => {
                            const titleEl = el.querySelector('a');
                            const descEl = el.querySelector('.snippet-description, .snippet-content');
                            if (titleEl && descEl) {
                                results.push({
                                    title: titleEl.textContent.trim(),
                                    url: titleEl.href,
                                    description: descEl.textContent.trim()
                                });
                            }
                        });
                        return results;
                    }
                """)

                results = []
                for r in results_data[:limit]:
                    results.append(SearchResult(
                        title=r['title'],
                        url=r['url'],
                        description=r['description'],
                        timestamp=datetime.now(UTC).isoformat()
                    ))

                return results

            finally:
                await browser.close()

    async def _search_duckduckgo(self, query: str, limit: int, **kwargs) -> List[SearchResult]:
        """HTTP-based DuckDuckGo search"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            headers = {'User-Agent': self.ua.random}
            
            # Build DuckDuckGo URL with parameters
            search_params = {'q': query}
            
            # DuckDuckGo supports some region filtering
            if kwargs.get('country'):
                # DuckDuckGo uses region codes like us-en, uk-en, etc.
                country = kwargs['country'].lower()
                language = kwargs.get('language', 'en')
                search_params['kl'] = f"{country}-{language}"
                
            param_string = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in search_params.items()])
            url = f"https://duckduckgo.com/html/?{param_string}"
            
            logger.info(f"DuckDuckGo search URL: {url}")

            async with session.get(url, headers=headers) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')

                results = []
                for result in soup.select('.result')[:limit]:
                    title_el = result.select_one('.result__title a')
                    snippet_el = result.select_one('.result__snippet')

                    if title_el and snippet_el:
                        # Extract actual URL from DDG redirect
                        href = title_el['href']
                        actual_url = href
                        if href.startswith('//duckduckgo.com/l/?uddg='):
                            # Parse the actual URL from DDG redirect
                            try:
                                actual_url = href.split('uddg=')[1].split('&')[0]
                                actual_url = urllib.parse.unquote(actual_url)
                            except:
                                actual_url = href

                        results.append(SearchResult(
                            title=title_el.get_text().strip(),
                            url=actual_url,
                            description=snippet_el.get_text().strip(),
                            timestamp=datetime.now(UTC).isoformat()
                        ))

                return results

    async def _search_ddgs(self, query: str, limit: int, **kwargs) -> List[SearchResult]:
        """DDGS library-based search with full parameter support and Brave backend preference"""
        try:
            logger.info(f"Starting DDGS library search for: '{query}' with parameters: {kwargs}")
            
            # Prepare DDGS parameters
            search_params = {
                'max_results': limit
            }
            
            # Try Brave backend first (preferred) with supported parameters
            brave_compatible = True
            brave_params = search_params.copy()
            
            # Brave backend supports language and time, but not region
            if kwargs.get('language'):
                brave_params['language'] = kwargs['language']
                
            # Map recency_days to DDGS time parameter
            if kwargs.get('recency_days') is not None:
                recency = kwargs['recency_days']
                if recency == 1:
                    brave_params['time'] = 'day'
                elif recency <= 7:
                    brave_params['time'] = 'week'
                elif recency <= 30:
                    brave_params['time'] = 'month'
                elif recency <= 365:
                    brave_params['time'] = 'year'
                # -1 means no time filter, so we don't set time parameter
            
            # If country/region is specified, Brave backend doesn't support it
            if kwargs.get('country'):
                brave_compatible = False
                logger.info(f"Country filter '{kwargs['country']}' not compatible with Brave backend, will try DuckDuckGo")
                    
            # Choose search type based on source parameter
            search_method = 'text'  # default
            if kwargs.get('source'):
                source = kwargs['source'].lower()
                if source == 'news':
                    search_method = 'news'
                elif source in ['images', 'videos']:
                    search_method = source
                    
            # Try Brave backend first if compatible
            if brave_compatible:
                try:
                    brave_params['backend'] = 'brave'
                    logger.info(f"DDGS search - trying Brave backend, method: {search_method}, params: {brave_params}")
                    
                    ddgs = DDGS()
                    search_func = getattr(ddgs, search_method)
                    
                    # Execute search in a thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    raw_results = await loop.run_in_executor(
                        None, 
                        lambda: list(search_func(query, **brave_params))
                    )
                    
                    if raw_results:
                        logger.info(f"DDGS Brave backend successful: {len(raw_results)} results")
                        return self._convert_ddgs_results(raw_results, search_method)
                    
                except Exception as e:
                    logger.warning(f"DDGS Brave backend failed: {e}, trying DuckDuckGo backend")
            
            # Fallback to DuckDuckGo backend with full parameter support
            ddg_params = search_params.copy()
            
            if kwargs.get('country'):
                ddg_params['region'] = kwargs['country'].lower()
                
            if kwargs.get('language'):
                ddg_params['language'] = kwargs['language']
                
            # Map recency_days to DDGS time parameter for DDG
            if kwargs.get('recency_days') is not None:
                recency = kwargs['recency_days']
                if recency == 1:
                    ddg_params['time'] = 'day'
                elif recency <= 7:
                    ddg_params['time'] = 'week'
                elif recency <= 30:
                    ddg_params['time'] = 'month'
                elif recency <= 365:
                    ddg_params['time'] = 'year'
            
            ddg_params['backend'] = 'duckduckgo'
            logger.info(f"DDGS search - using DuckDuckGo backend, method: {search_method}, params: {ddg_params}")
            
            ddgs = DDGS()
            search_func = getattr(ddgs, search_method)
            
            # Execute search in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            raw_results = await loop.run_in_executor(
                None, 
                lambda: list(search_func(query, **ddg_params))
            )
            
            logger.info(f"DDGS DuckDuckGo backend completed: {len(raw_results)} results")
            return self._convert_ddgs_results(raw_results, search_method)
            
        except Exception as e:
            logger.error(f"DDGS search failed: {e}")
            raise e
    
    def _convert_ddgs_results(self, raw_results: list, search_method: str) -> List[SearchResult]:
        """Convert DDGS results to our SearchResult format"""
        results = []
        for item in raw_results:
            if search_method == 'news':
                # News results have: date, title, body, url, image, source
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    description=item.get('body', ''),
                    timestamp=item.get('date', datetime.now(UTC).isoformat())
                ))
            else:
                # Text results have: title, href, body
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('href', ''),
                    description=item.get('body', ''),
                    timestamp=datetime.now(UTC).isoformat()
                ))
        return results

    async def _extract_content_concurrent(self, results: List[SearchResult],
                                        max_content_length: Optional[int]) -> None:
        """Extract content from multiple URLs concurrently"""
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def extract_with_semaphore(result: SearchResult):
            async with semaphore:
                try:
                    content = await self._extract_page_content(result.url, max_content_length)
                    result.full_content = content
                    result.content_preview = content[:500] + "..." if len(content) > 500 else content
                    result.word_count = len(content.split())
                    result.fetch_status = "success"
                except Exception as e:
                    result.fetch_status = "error"
                    result.error = str(e)
                    logger.warning(f"Content extraction failed for {result.url}: {e}")

        await asyncio.gather(*[extract_with_semaphore(r) for r in results])

    async def _extract_page_content(self, url: str, max_content_length: Optional[int]) -> str:
        """Extract readable content from a webpage"""
        try:
            # Try fast HTTP extraction first
            content = await self._extract_with_httpx(url, max_content_length)
            if self._is_meaningful_content(content):
                return content
        except Exception as e:
            logger.debug(f"HTTP extraction failed for {url}: {e}")

        # Fallback to browser extraction
        return await self._extract_with_browser(url, max_content_length)

    async def _extract_with_httpx(self, url: str, max_content_length: Optional[int]) -> str:
        """Fast HTTP-based content extraction"""
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={'User-Agent': self.ua.random})
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'ads', '.ad', '.advertisement']):
                tag.decompose()

            # Extract main content
            content = ""
            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                text = tag.get_text().strip()
                if text and len(text) > 20:  # Filter short fragments
                    content += text + "\n\n"

            content = content.strip()
            if max_content_length and len(content) > max_content_length:
                content = content[:max_content_length]

            return content

    async def _extract_with_browser(self, url: str, max_content_length: Optional[int]) -> str:
        """Browser-based content extraction for dynamic sites"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=self.ua.random,
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()

                await page.goto(url, wait_until='networkidle')
                await page.wait_for_timeout(2000)  # Wait for dynamic content

                # Extract readable text content
                content = await page.evaluate("""
                    () => {
                        // Remove unwanted elements
                        const elements = document.querySelectorAll('script, style, nav, header, footer, aside, .ad, .advertisement');
                        elements.forEach(el => el.remove());
                        
                        // Extract main content
                        const contentSelectors = ['main', 'article', '.content', '.post', '.entry', '#content', '#main'];
                        let content = '';
                        
                        for (const selector of contentSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                content = element.textContent.trim();
                                break;
                            }
                        }
                        
                        // Fallback to body text
                        if (!content) {
                            content = document.body.textContent.trim();
                        }
                        
                        return content;
                    }
                """)

                if max_content_length and len(content) > max_content_length:
                    content = content[:max_content_length]

                return content

            finally:
                await browser.close()

    def _assess_result_quality(self, results: List[SearchResult], query: str) -> float:
        """Assess search result quality (0.0 to 1.0)"""
        if not results:
            return 0.0

        # Simple quality metrics
        query_words = set(query.lower().split())
        total_score = 0.0

        for result in results:
            title_words = set(result.title.lower().split())
            desc_words = set(result.description.lower().split())

            # Relevance score based on word overlap
            relevance = len(query_words & (title_words | desc_words)) / len(query_words)
            total_score += relevance

        return min(total_score / len(results), 1.0)

    def _is_meaningful_content(self, content: str) -> bool:
        """Check if extracted content is meaningful"""
        if len(content) < 100:
            return False

        # Check for common bot detection messages
        bot_indicators = ['captcha', 'blocked', 'access denied', 'robot', 'verification', '403', 'forbidden']
        content_lower = content.lower()

        for indicator in bot_indicators:
            if indicator in content_lower:
                return False

        return True

    def _result_to_dict(self, result: SearchResult) -> Dict[str, Any]:
        """Convert SearchResult to dictionary"""
        return {
            "title": result.title,
            "url": result.url,
            "description": result.description,
            "full_content": result.full_content,
            "content_preview": result.content_preview,
            "word_count": result.word_count,
            "timestamp": result.timestamp,
            "fetch_status": result.fetch_status,
            "error": result.error
        }