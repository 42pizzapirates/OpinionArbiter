from dataclasses import dataclass, field
from typing import Any, Optional


# 第一组：元数据
@dataclass(slots=True)
class Engagement:
    """互动数据(点赞/评论/转发/收藏/回复)"""
    likes: float = 0.0
    comments: float = 0.0
    shares: float = 0.0
    collects: float = 0.0
    replies: float = 0.0


@dataclass(slots=True)
class RetrievalMeta:
    """召回过程元数据(命中的查询词/通道/各通道分数)。"""

    # 召回来源
    matched_queries: list[str] = field(default_factory=list)
    retrieval_channels: list[str] = field(default_factory=list)

    # 召回质量
    retrieval_scores: dict[str, float] = field(default_factory=dict)


# 第二组：核心业务实体
@dataclass(slots=True)
class EvidenceRecord:
    """证据记录:双通道DB/Milvus 召回的统一数据载体。"""
    # 溯源身份标识
    id: str
    platform: str
    source_table: str
    source_keyword: Optional[str]

    # 核心业务内容
    content: str
    published_at: str

    # 打分状态
    hotness_score: float
    final_score: float = 0.0

    # 拓扑对象
    cluster_id: str = ""
    engagement: Engagement = field(default_factory=Engagement)
    retrieval: RetrievalMeta = field(default_factory=RetrievalMeta)


# 第三组：全局容器与聚合根
@dataclass(slots=True)
class EvidenceCluster:
    """证据聚类簇（组）"""

    # 簇基础描述
    id: str
    label: str
    summary: str

    # 簇成员
    member_record_ids: list[str] = field(default_factory=list)
    representative_ids: list[str] = field(default_factory=list)
    size: int = 0


@dataclass(slots=True)
class EvidencePool:
    """全局证据池。"""
    query: str

    # 资产清单
    records: list[EvidenceRecord] = field(default_factory=list)
    clusters: list[EvidenceCluster] = field(default_factory=list)


