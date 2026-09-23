from typing import Any

from engines.common.runtime.call_retry import with_retry
from engines.contracts.config import get_settings
from engines.media_agent.web_search.base import BaseSearchClient
from engines.media_agent.web_search.schemas import (
    SearchProviderResponse,
    WebpageResult,
)


class TavilySearchClient(BaseSearchClient):
    """Tavily Web 检索 Provider 实现。"""

    def __init__(self) -> None:
        """配置 Tavily 密钥与接口地址及请求头。"""
        super().__init__()
        self.api_key = get_settings().TAVILY_API_KEY
        self.base_url = get_settings().TAVILY_BASE_URL
        self._headers = self.build_request_headers(self.api_key, accept="application/json")

    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        """深度检索,取 10 条高级结果。"""
        return await self._execute_search(query=query, max_results=10, search_depth="advanced")

    async def source_search(self, query: str) -> SearchProviderResponse:
        """基础溯源检索,取 5 条结果。"""
        return await self._execute_search(query=query, max_results=5, search_depth="basic")

    async def realtime_search(self, query: str) -> SearchProviderResponse:
        """追加实时词并限一周新闻主题检索。"""
        return await self._execute_search(
            query=f"{query} 最新进展", max_results=5, time_range="week", topic="news"
        )

    @with_retry
    async def _execute_search(
            self,
            query: str,
            max_results: int,
            search_depth: str | None = None,
            time_range: str | None = None,
            topic: str = "general",
    ) -> SearchProviderResponse:
        """带重试地组装负载发起 POST 并解析。"""
        payload: dict[str, object] = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth or "basic",
            "topic": topic,
        }
        if time_range:
            payload["time_range"] = time_range
            payload["days"] = 7
        response = await self.send_request(
            "POST",
            self.base_url,
            {"headers": self._headers, "json": payload},
        )
        return self._process_response(response, query)

    @staticmethod
    def _process_response(response_dict: dict[str, Any], query: str) -> SearchProviderResponse:
        """将 Tavily 原始结果映射为网页模型。"""
        results = response_dict.get("results", [])
        webpages: list[WebpageResult] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            webpages.append(
                WebpageResult(
                    title=result.get("title"),
                    url=result.get("url"),
                    content=result.get("content"),
                    date=result.get("published_date"),
                )
            )
        return SearchProviderResponse(
            query=query,
            provider="tavily",
            webpages=webpages,
        )
