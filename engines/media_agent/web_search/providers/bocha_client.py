import json

from loguru import logger

from engines.contracts.config import get_settings
from engines.media_agent.web_search.base import BaseSearchClient
from engines.media_agent.web_search.schemas import (
    SearchProviderResponse,
    WebpageResult,
)


class BochaSearchClient(BaseSearchClient):
    """Bocha Web 检索 Provider 实现。"""

    def __init__(self) -> None:
        """读取 Bocha 密钥与地址并构建请求头。"""
        super().__init__()
        self.api_key = get_settings().BOCHA_API_KEY
        self.base_url = get_settings().BOCHA_BASE_URL
        self._headers = self.build_request_headers(self.api_key, accept="*/*")

    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        """全量检索,取 15 条网页结果。"""
        return await self._execute_search(query=query, count=15)

    async def source_search(self, query: str) -> SearchProviderResponse:
        """溯源检索,取 10 条网页结果。"""
        return await self._execute_search(query=query, count=10)

    async def realtime_search(self, query: str) -> SearchProviderResponse:
        """限一周新鲜度并取 5 条实时结果。"""
        return await self._execute_search(
            query=query,
            count=5,
            freshness="oneWeek",
        )

    async def _execute_search(
        self,
        query: str,
        count: int,
        freshness: str | None = None,
    ) -> SearchProviderResponse:
        """组装负载发起 POST 并解析响应。"""
        payload: dict[str, object] = {
            "stream": False,
            "query": query,
            "count": count,
        }
        if freshness is not None:
            payload["freshness"] = freshness
        response = await self.send_request(
            "POST",
            self.base_url,
            {"headers": self._headers, "json": payload},
        )
        return self._process_response(response, query)

    @staticmethod
    def _process_response(response_dict: dict[str, object], query: str) -> SearchProviderResponse:
        """从消息流抽取网页来源并映射为模型。"""
        webpages: list[WebpageResult] = []
        raw_messages = response_dict.get("messages", [])
        messages = raw_messages if isinstance(raw_messages, list) else []
        for message in messages:
            if (
                not isinstance(message, dict)
                or message.get("role") != "assistant"
                or message.get("type") != "source"
                or message.get("content_type") != "webpage"
            ):
                continue
            raw_content = message.get("content")
            if not isinstance(raw_content, str):
                continue
            try:
                content = json.loads(raw_content)
            except json.JSONDecodeError as exc:
                logger.warning(f"[media] Bocha 网页来源解析失败: {exc}")
                continue
            results = content.get("value", [])
            for item in results:
                if not isinstance(item, dict):
                    continue
                webpages.append(
                    WebpageResult(
                        title=item.get("name"),
                        url=item.get("url"),
                        content=item.get("snippet"),
                        date=item.get("dateLastCrawled"),
                    )
                )
        return SearchProviderResponse(
            query=query,
            provider="bocha",
            webpages=webpages,
        )
