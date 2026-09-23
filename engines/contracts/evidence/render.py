from engines.contracts.evidence.models import Engagement, EvidenceRecord
from engines.contracts.evidence.models import EvidenceStrength

_ENGAGEMENT_LABELS = {
    "likes": "点赞",
    "comments": "评论",
    "shares": "转发",
    "collects": "收藏",
    "replies": "回复",
}


def evaluate_evidence_strength(hit_count: int) -> EvidenceStrength:
    """按命中数评估证据强度等级"""
    if hit_count >= 10:
        return "strong"
    if hit_count >= 5:
        return "medium"
    if hit_count > 0:
        return "weak"
    return "missing"


def render_evidence_records(records: list[EvidenceRecord]) -> list[str]:
    """渲染证据记录为 LLM 证据文本块"""
    return [_render_single_record(record) for record in records]


def _render_single_record(record: EvidenceRecord) -> str:
    """渲染单条证据记录为文本"""
    lines = [f"标题: {record.content[:30]}"]
    lines.append(f"平台: {record.platform}")
    lines.append(f"来源表/工具: {record.source_table}")
    lines.append(f"来源关键词: {record.source_keyword}")
    lines.append(f"内容: {_limit_content(record.content)}")
    lines.append(f"发布时间/抓取时间: {record.published_at}")
    if record.hotness_score:
        lines.append(f"热度分: {record.hotness_score}")
    if record.final_score:
        lines.append(f"综合分: {record.final_score}")
    if record.engagement:
        lines.append(f"互动数据: { _format_engagement(record.engagement)}")
    if record.url:
        lines.append(f"链接: {record.url}")
    return "\n".join(lines)


def _limit_content(content: str, max_length: int = 3000) -> str:
    """超长内容截断并加省略号"""
    if len(content) <= max_length:
        return content
    truncated = content[:max_length]
    return truncated + "..."


def _format_engagement(engagement: Engagement) -> str:
    """将互动数据格式化为中文标签串"""
    parts = [
        f"{label} {value}"
        for key, label in _ENGAGEMENT_LABELS.items()
        if (value := getattr(engagement, key))
    ]
    return " / ".join(parts)
