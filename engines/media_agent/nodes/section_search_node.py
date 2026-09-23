from typing import Any

from loguru import logger

from engines.common.nodes.base_node import BaseNode
from engines.contracts.evidence.models import EvidenceRecord
from engines.contracts.roles import role_display_name
from engines.media_agent.state import MediaState, MediaSection


class SearchNode(BaseNode):
    """遍历章节组合关键词检索并聚合去重证据。"""

    async def __call__(self, state: MediaState) -> dict[str, Any]:
        """遍历章节执行检索并去重产出证据池。"""
        agent_name = role_display_name(state['role'])  # type: ignore
        self.context.report_progress("searching", f"{agent_name} 开始执行公域信息搜索", 30)
        query = state.get("query")
        sections: list[MediaSection] = state.get("sections")
        search_evidence_records = []
        seen_keys = set()
        executed_queries = []

        for section in sections:
            tool = section.get("search_tool", "comprehensive_search")
            search_query = f"{query} {' '.join(section.get('search_keywords'))}".strip()  # type: ignore
            records: list[EvidenceRecord] = await self.context.execute_search(tool, search_query)  # type: ignore
            executed_queries.append(f"[{tool}] {search_query}")
            for record in records:
                unique_key = record.id
                if unique_key not in seen_keys:
                    seen_keys.add(unique_key)
                    search_evidence_records.append(record)
        self.context.report_progress("searching", f"{agent_name} 执行公域信息搜索完成", 40)
        return {"search_evidence_records": search_evidence_records}
