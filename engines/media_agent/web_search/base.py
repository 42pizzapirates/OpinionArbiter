from abc import ABC, abstractmethod
from typing import Any, TypedDict

import httpx

from engines.media_agent.web_search.schemas import SearchProviderResponse


class HttpRequestOptions(TypedDict, total=False):
    """统一 HTTP 请求的参数选项类型。"""

    headers: dict[str, str]
    params: dict[str, Any]
    json: dict[str, Any]


class BaseSearchClient(ABC):
    """Web 搜索 Provider 的抽象能力基类。"""

    def __init__(self):
        """基类空构造,子类完成具体初始化。"""

    @staticmethod
    def build_request_headers(api_key: str, *, accept: str = "application/json") -> dict[str, str]:
        """构造 Bearer JSON 请求头。"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": accept,
        }
        return headers

    async def send_request(
        self,
        method: str,
        url: str,
        kwargs: HttpRequestOptions,
    ) -> dict[str, Any]:
        """用 httpx 异步发起请求并返回 JSON。"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=kwargs.get("headers"),
                params=kwargs.get("params"),
                json=kwargs.get("json"),
            )
            data = response.json()
        return data

    @abstractmethod
    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        """综合检索某主题的全面公开媒体信息。"""

    @abstractmethod
    async def source_search(self, query: str) -> SearchProviderResponse:
        """溯源检索可核查的原始网页出处。"""

    @abstractmethod
    async def realtime_search(self, query: str) -> SearchProviderResponse:
        """实时检索最新报道与传播动态。"""
