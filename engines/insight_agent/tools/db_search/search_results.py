from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SearchRecord:
    """单条数据库召回的标准化检索记录。"""

    mysql_pk: str
    platform: str
    source_table: str
    title_or_content: str
    published_at: datetime

    source_keyword: Optional[str] = None
    engagement: dict[str, float] = field(default_factory=dict)
    hotness_score: Optional[float] = None


@dataclass
class SearchResponse:
    """单通道召回结果集合与统计信息。"""

    retrieval_channel: str
    search_results: list[SearchRecord] = field(default_factory=list)
    search_results_count: int = 0
    search_error_message: Optional[str] = None
