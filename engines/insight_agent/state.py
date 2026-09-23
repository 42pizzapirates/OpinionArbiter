from typing import TypedDict

from engines.contracts.evidence.models import EvidenceStrength
from engines.insight_agent.evidence_processor import EvidencePool, EvidenceRecord


class InsightSection(TypedDict, total=False):
    """单章节交付物：标题、目标、正文与证据强度。"""

    title: str
    goal: list[str]
    section_key: str

    body: str
    hit_count: int
    evidence_strength: EvidenceStrength


class InsightState(TypedDict, total=False):
    """LangGraph 全局状态：证据池、章节列表与游标。"""

    query: str
    role: str
    evidence_pool: EvidencePool

    sections: list[InsightSection]
    section_evidence_records: list[list[EvidenceRecord]]

    cursor: int

    final_report: str
    report_title: str
