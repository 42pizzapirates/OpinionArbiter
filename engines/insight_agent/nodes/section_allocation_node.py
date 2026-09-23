from typing import Any

from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.insight_agent.evidence_processor import (
    EvidencePool,
    EvidenceRecord,
    generate_section_records,
)
from engines.insight_agent.state import InsightSection, InsightState


class SectionAllocationNode(BaseNode):
    """证据分配节点：按章节键为各章节配置证据。"""

    def __init__(self, context: ResearchNodeContext) -> None:
        """初始化证据分配节点上下文。"""
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """为每个章节筛选并截取对应证据记录。"""
        pool: EvidencePool = state["evidence_pool"]
        records = pool.records
        sections: list[InsightSection] = list(state.get("sections"))
        section_evidence_records: list[list[EvidenceRecord]] = []
        for section in sections:
            section_key = section["section_key"]
            section_records = generate_section_records(section_key, records)[:20]
            section_evidence_records.append(section_records)
        return {"sections": sections, "section_evidence_records": section_evidence_records}
