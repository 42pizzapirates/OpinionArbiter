from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping

from loguru import logger

from engines.common.eventing.event import SectionReadyEvent
from engines.common.eventing.publishers import publish_section_read_ready
from engines.contracts.dimensions import dimension_for_key
from engines.contracts.roles import ROLE_INFOS
from engines.contracts.evidence.models import EvidenceRecord, EvidenceStrength
from engines.contracts.evidence.render import (
    evaluate_evidence_strength,
    render_evidence_records,
)


@dataclass(slots=True)
class EvidenceCluster:
    """证据聚类簇：同维度证据的语义分组与代表样本。"""
    id: str
    label: str
    summary: str
    member_record_ids: list[str] = field(default_factory=list)
    representative_ids: list[str] = field(default_factory=list)
    size: int = 0


@dataclass(slots=True)
class EvidencePool:
    """私域证据池：承载全部召回记录与聚类结果。"""
    query: str
    records: list[EvidenceRecord] = field(default_factory=list)
    clusters: list[EvidenceCluster] = field(default_factory=list)


@dataclass(slots=True)
class SectionEvidencePack:
    """章节证据包：渲染后的证据块与论证强度。"""
    used_query: str = ""
    evidence_count: int = 0
    strength: EvidenceStrength = "missing"
    evidence_source_blocks: list[str] = field(default_factory=list)


def generate_plan_overview(pool: EvidencePool) -> dict[str, Any]:
    """统计记录总数、平台分布与聚类代表观点供规划使用。"""
    records_by_id = {r.id: r for r in pool.records if r.id}
    dimension_clusters: list[dict[str, Any]] = []
    for cluster in pool.clusters:
        representative_quotes = []
        for record_id in cluster.representative_ids[:3]:
            record = records_by_id.get(record_id)
            if record is None:
                continue
            representative_quotes.append(
                {
                    "platform": record.platform,
                    "content": record.content[:150],
                }
            )
        dimension_clusters.append(
            {
                "dimension_goal": _resolve_dimension_goal(cluster.id),
                "label": cluster.label,
                "size": cluster.size,
                "representative_quotes": representative_quotes,
            }
        )
    return {
        "total_records": len(pool.records),
        "platform_distribution": dict(Counter(r.platform for r in pool.records)),
        "dimension_clusters": dimension_clusters,
    }


def _resolve_dimension_goal(cluster_id: str) -> str:
    """依据聚类键解析对应私域维度的分析目标。"""
    dimension = dimension_for_key(cluster_id.removeprefix("cluster_"))
    return dimension.insight_goal if dimension else ""


def generate_section_records(
    section_key: str, records: list[EvidenceRecord]
) -> list[EvidenceRecord]:
    """按章节键筛选证据并按评论分或热度分降序排列。"""
    matched_records = [r for r in records if r.cluster_id == f"cluster_{section_key}"]
    if not matched_records:
        return []
    sort_key = (
        _calculate_comment_score
        if section_key in {"sentiment_and_opinion", "deep_causes_and_impact"}
        else _calculate_heat_score
    )
    return sorted(matched_records, key=sort_key, reverse=True)


def _calculate_comment_score(record: EvidenceRecord) -> float:
    """评论分：综合正文长度、回复与点赞加权计算。"""
    eng = record.engagement
    score = (
        float(record.final_score)
        + min(len(record.content) / 100, 1.0) * 0.5
        + min(float(eng.replies) / 5, 1.0) * 0.3
        + min(float(eng.likes) / 500, 1.0) * 0.2
    )
    return round(score, 3)


def _calculate_heat_score(record: EvidenceRecord) -> float:
    """热度分：热度分加最终分加权计算。"""
    score = float(record.hotness_score) + float(record.final_score) * 0.1
    return round(score, 3)


def generate_section_evidence_pack(
    used_query: str,
    selected: list[EvidenceRecord],
) -> SectionEvidencePack:
    """渲染选定证据并评估论证强度，组装章节证据包。"""
    count = len(selected)
    return SectionEvidencePack(
        used_query=used_query,
        evidence_count=count,
        strength=evaluate_evidence_strength(count),
        evidence_source_blocks=render_evidence_records(selected),
    )


def dispatch_section_ready_event(
    state: Mapping[str, Any], section_index: int, section: Mapping[str, Any]
) -> None:
    """发布章节就绪事件，通知下游消费章节正文与证据。"""
    role_key = state.get("role", "insight")
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
        logger.info(f"【{agent_name}】 [section_ready] 事件已发布 章节={event.section_key} 证据包数={event.section_metadata['hit_count']}")
    except Exception as exc:
        logger.warning(f"【{agent_name}】 [section_ready] 事件发布失败: {exc}")
