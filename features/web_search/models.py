"""
Models for the web search feature
"""

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    """Current time as an ISO 8601 string in UTC"""
    return datetime.now(UTC).isoformat()


@dataclass
class SearchResult:
    """A single search result, optionally with extracted page content"""
    title: str
    url: str
    description: str
    full_content: str = ""
    content_preview: str = ""
    word_count: int = 0
    timestamp: str = field(default_factory=utc_now_iso)
    fetch_status: str = "success"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary"""
        return asdict(self)
