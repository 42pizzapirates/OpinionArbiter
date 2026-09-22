from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SectionResult:
    """单 Agent 维度章节结果(事件载荷投影)。"""
    source: str
    section_key: str
    title: str
    body: str
    query: str = ""
    hit_count: int = 0
    strength: str = ""

    @classmethod
    def from_event(cls, data: dict[str, Any]) -> "SectionResult":
        """从 section_ready 事件载荷构造"""
        metadata = data.get("section_metadata")
        return cls(
            source=data["source"],
            section_key=data["section_key"],
            title=data["title"],
            body=data["body"],
            query=data["query"],
            hit_count=metadata.get("hit_count"),
            strength=metadata.get("strength"),
        )


@dataclass(frozen=True)
class SectionPair:
    """同维度 insight/media 配对,供主持人研判。"""

    section_key: str
    title: str
    insight: SectionResult
    media: SectionResult


@dataclass(frozen=True)
class SectionJudgement:
    """主持人单维度研判发言(Markdown 正文)。"""

    section_key: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        """序列化为含维度键与研判正文的字典。"""
        return {"section_key": self.section_key, "content": self.content}
