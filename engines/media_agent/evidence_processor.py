from dataclasses import dataclass, field
from typing import Any, Mapping

from loguru import logger

from engines.common.eventing.event import SectionReadyEvent
from engines.common.eventing.publishers import publish_section_read_ready
from engines.contracts.evidence.models import EvidenceRecord
from engines.contracts.evidence.render import (
    EvidenceStrength,
    evaluate_evidence_strength,
    render_evidence_records,
)
from engines.contracts.roles import ROLE_INFOS


@dataclass(frozen=True, slots=True)
class SectionEvidencePack:
    """章节证据组装结果,供节点写回章节字段。"""

    used_query: str
    evidence_count: int
    evidence_strength: EvidenceStrength = "missing"
    evidence_source_blocks: list[str] = field(default_factory=list)


def generate_section_evidence_pack(
        used_query: str,
        records: list[EvidenceRecord],
) -> SectionEvidencePack:
    """按命中数渲染证据块并评估证据强度。"""
    hit_count = len(records)
    return SectionEvidencePack(
        used_query=used_query,
        evidence_count=hit_count,
        evidence_source_blocks=render_evidence_records(records),
        evidence_strength=evaluate_evidence_strength(hit_count),
    )


def dispatch_section_ready_event(
        state: Mapping[str, Any],
        section_index: int,
        section: Mapping[str, Any],
) -> None:
    """发布章节就绪事件供下游消费与展示。"""
    role_key = state.get("role", "media")
    role_info = ROLE_INFOS.get(role_key)
    agent_name = role_info.display_name
    try:
        section_metadata = {
            "hit_count": section.get("hit_count", 0),
            "evidence_strength": section.get("evidence_strength", "missing"),
        }
        event = SectionReadyEvent(
            source=role_key,
            agent_name=agent_name,
            section_key=section.get("section_key"),
            section_index=section_index,
            title=section.get("title"),
            query=state.get("query"),
            body=section.get("body"),
            section_metadata=section_metadata,
        )
        publish_section_read_ready(event)
        logger.info(
            f"【{agent_name}】 [section_ready] 事件已发布 章节={event.section_key} 证据包数={event.section_metadata['hit_count']}")

    except Exception as exc:
        logger.warning(f"【{agent_name}】 section_ready 事件发布失败: {exc}")
