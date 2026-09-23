import datetime
from typing import Any

from engines.contracts.config import get_settings
from engines.media_agent.web_search.base import BaseSearchClient
from engines.media_agent.web_search.schemas import (
    SearchProviderResponse,
    WebpageResult,
)

AUTHORITATIVE_SOURCES = "news.cctv.com"
SOCIAL_SOURCES = "weibo.com,zhihu.com,toutiao.com"


class AnspireSearchClient(BaseSearchClient):
    """Anspire Web 检索 Provider 实现。"""

    def __init__(self) -> None:
        """读取 Anspire 密钥与地址并构建请求头。"""
        super().__init__()
        self.api_key = get_settings().ANSPIRE_API_KEY
        self.base_url = get_settings().ANSPIRE_BASE_URL
        self._headers = self.build_request_headers(self.api_key, accept="application/json")

    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        """全量检索,不限站点,取 15 条。"""
        return await self._execute_search(query=query, top_k=15, insite="")

    async def source_search(self, query: str) -> SearchProviderResponse:
        """强化官方词并在央视站点溯源检索。"""
        enhanced_query = f"{query} 通报 OR 回应 OR 官方"
        return await self._execute_search(
            query=enhanced_query, top_k=10, insite=AUTHORITATIVE_SOURCES
        )

    async def realtime_search(self, query: str) -> SearchProviderResponse:
        """限一周内社交站点并强化实时词检索。"""
        to_time = datetime.datetime.now()
        from_time = to_time - datetime.timedelta(weeks=1)
        enhanced_query = f"{query} 最新 OR 热搜"
        return await self._execute_search(
            query=enhanced_query,
            top_k=10,
            insite=SOCIAL_SOURCES,
            from_time=from_time.strftime("%Y-%m-%d %H:%M:%S"),
            to_time=to_time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    async def _execute_search(
        self,
        query: str,
        top_k: int,
        insite: str,
        from_time: str = "",
        to_time: str = "",
    ) -> SearchProviderResponse:
        """组装参数发起 GET 并解析响应。"""
        params = {
            "query": query,
            "top_k": top_k,
            "Insite": insite,
            "FromTime": from_time,
            "ToTime": to_time,
        }
        response = await self.send_request(
            "GET",
            self.base_url,
            {"headers": self._headers, "params": params},
        )
        return self._process_response(response, query)

    @staticmethod
    def _process_response(response_dict: dict[str, Any], query: str) -> SearchProviderResponse:
        """将 Anspire 原始结果映射为网页模型。"""
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
                    date=result.get("date"),
                )
            )
        return SearchProviderResponse(
            query=query,
            provider="anspire",
            webpages=webpages,
        )
