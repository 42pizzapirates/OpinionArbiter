import hashlib
from typing import Callable, get_args

from loguru import logger

from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate
from engines.contracts.evidence.models import EvidenceRecord
from engines.media_agent.web_search.factory import WebSearchClient
from engines.media_agent.web_search.schemas import SearchProviderResponse, SearchTool


class MediaContext:
    """公开媒体研究员的依赖容器与 Web 检索入口。"""

    def __init__(
            self,
            role: str,
            llm_client: LLMClient,
            output_dir: str,
            progress_callback: Callable[[ProgressUpdate], None] | None = None,
    ) -> None:
        """注入角色与 LLM 并创建 Web 搜索客户端。"""
        self.role = role
        self.llm_client = llm_client
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        self._web_search_client = WebSearchClient()

    def report_progress(self, status: str, message: str, pct: int) -> None:
        """向外推送研究进度状态、消息与百分比。"""
        self.progress_callback(ProgressUpdate(status, message, pct))

    async def execute_search(self, tool_name: SearchTool, query: str) -> list[EvidenceRecord]:
        """执行 Web 检索并将结果映射为证据记录列表。"""
        validated_tool: SearchTool = (
            tool_name if tool_name in get_args(SearchTool) else "comprehensive_search"
        )
        try:
            web_response = await self._search_webpage(validated_tool, query)
            return self._map_to_evidence_records(web_response, query)
        except Exception as exc:
            logger.error(f"{self.role} 搜索失败 tool={validated_tool} query={query} 异常={exc}")
            return []

    async def _search_webpage(
            self,
            tool_name: SearchTool,
            query: str,
    ) -> SearchProviderResponse:
        """按工具类型分派综合、溯源或实时检索。"""
        match tool_name:
            case "source_search":
                response = await self._web_search_client.source_search(query)
            case "realtime_search":
                response = await self._web_search_client.realtime_search(query)
            case _:
                response = await self._web_search_client.comprehensive_search(query)
        return response

    def _map_to_evidence_records(
            self,
            response: SearchProviderResponse,
            query: str,
    ) -> list[EvidenceRecord]:
        """将网页结果映射为带哈希 ID 的证据记录。"""
        if response is None:
            return []
        return [
            EvidenceRecord(
                id=_generate_content_hash_id(page.content, page.url),
                platform=response.provider,
                source_table=response.provider,
                source_keyword=query,
                content=page.content,
                published_at=page.date,
                url=page.url,
            )
            for page in response.webpages
        ]


def _generate_content_hash_id(content: str, url: str) -> str:
    """对内容与 URL 做 MD5 生成证据唯一标识。"""
    raw_key = content + url
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()  # type: ignore
