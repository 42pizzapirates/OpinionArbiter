from dataclasses import dataclass, field
from typing import Literal, Optional

EvidenceStrength = Literal["missing", "weak", "medium", "strong"]


@dataclass(slots=True)
class Engagement:
    """证据互动数据(点赞/评论/转发等)"""

    likes: float = 0.0
    comments: float = 0.0
    shares: float = 0.0
    collects: float = 0.0
    replies: float = 0.0


@dataclass(slots=True)
class RetrievalMeta:
    """召回过程元数据(查询词/通道/分数)"""

    matched_queries: list[str] = field(default_factory=list)
    retrieval_channels: list[str] = field(default_factory=list)
    retrieval_scores: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class EvidenceRecord:
    """统一证据记录(DB/向量/网页召回载体)"""

    id: str
    platform: str
    source_table: str
    source_keyword: Optional[str]

    content: str
    published_at: str

    hotness_score: float = 0.0
    final_score: float = 0.0

    cluster_id: str = ""
    engagement: Engagement = field(default_factory=Engagement)
    retrieval: RetrievalMeta = field(default_factory=RetrievalMeta)

    url: str = ""
