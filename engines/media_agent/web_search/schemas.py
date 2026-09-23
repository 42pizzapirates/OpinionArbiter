from dataclasses import dataclass, field
from typing import Literal

SearchTool = Literal["comprehensive_search", "source_search", "realtime_search"]
SearchProvider = Literal["anspire", "bocha", "tavily"]


@dataclass(frozen=True, slots=True)
class WebpageResult:
    """单条网页检索结果的领域模型。"""

    title: str
    url: str
    content: str
    date: str


@dataclass(frozen=True, slots=True)
class SearchProviderResponse:
    """Provider 检索结果的统一响应模型。"""

    query: str
    provider: SearchProvider
    webpages: list[WebpageResult] = field(default_factory=list)
