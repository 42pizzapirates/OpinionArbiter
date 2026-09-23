from typing import TypedDict

from engines.contracts.evidence.models import EvidenceRecord
from engines.contracts.evidence.render import EvidenceStrength
from engines.media_agent.web_search.schemas import SearchTool


class MediaSection(TypedDict, total=False):
    """一个章节的规划与研究字段的聚合状态。"""

    title: str
    section_key: str
    goal: list[str]
    search_tool: SearchTool
    search_keywords: list[str]
    body: str
    hit_count: int
    evidence_strength: EvidenceStrength


class MediaState(TypedDict, total=False):
    """媒体智能体 LangGraph 全局状态定义。"""

    query: str
    role: str
    search_evidence_records: list[EvidenceRecord]
    sections: list[MediaSection]
    cursor: int
    final_report: str
    report_title: str
