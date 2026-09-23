import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional

import jieba.analyse
from loguru import logger

from engines.contracts.config import get_settings
from engines.contracts.evidence.models import Engagement, EvidenceRecord, RetrievalMeta
from engines.insight_agent.tools.db_search.repository import DatabaseSearchRepository
from engines.insight_agent.tools.db_search.search_results import (
    SearchRecord,
    SearchResponse,
)
from engines.insight_agent.tools.vector_search.repository import VectorSearchRepository
from engines.insight_agent.tools.vector_search.search_results import SearchHit

RetrievalChannel = Literal["keyword_recall", "comment_recall", "hot_recall"]


@dataclass(slots=True)
class RetrievalQueryTask:
    """单条召回任务及其通道权重与配额。"""

    channel: RetrievalChannel
    limit: int
    channel_score: float
    query: str = ""


def build_retrieval_tasks(query: str) -> list[RetrievalQueryTask]:
    """按原句与分词构建三通道召回任务列表。"""
    final_query = []
    final_query.append(query)
    for extract_kw in _extract_keywords(query):
        if extract_kw not in final_query:
            final_query.append(extract_kw)
    retrieval_tasks: list[RetrievalQueryTask] = []
    for keyword in final_query:
        retrieval_tasks.append(
            RetrievalQueryTask(channel="keyword_recall", limit=10, channel_score=0.5, query=keyword)
        )
        retrieval_tasks.append(
            RetrievalQueryTask(channel="comment_recall", limit=5, channel_score=0.4, query=keyword)
        )
    retrieval_tasks.append(
        RetrievalQueryTask(channel="hot_recall", channel_score=0.3, limit=5, query=query)
    )
    return retrieval_tasks


def _extract_keywords(query: str) -> list[str]:
    """用 jieba 抽取查询关键词用于多通道召回。"""
    return [keyword for keyword in jieba.analyse.extract_tags(query, 2) if 2 <= len(keyword) <= 4]


class InsightRetrivalService:
    """编排 MySQL 与 Milvus 检索并归一化为证据。"""

    def __init__(self):
        self._db_repo = DatabaseSearchRepository()
        self._vec_repo = VectorSearchRepository()

    async def retrival_evidence(self, query: str) -> list[EvidenceRecord]:
        """并发执行三通道召回与向量检索并合并证据。"""
        retrival_db_tasks = build_retrieval_tasks(query)
        db_evidences, vec_evidences = await asyncio.gather(
            self._retrival_db_evidence(retrival_db_tasks), self._retrival_vec_evidence(query)
        )
        return [*db_evidences, *vec_evidences]

    async def _retrival_vec_evidence(self, query) -> list[EvidenceRecord]:
        """执行 Milvus 混合检索并转换为证据记录。"""
        if not get_settings().INSIGHT_VECTOR_ENABLED:
            return []
        try:
            search_results = await asyncio.to_thread(
                self._vec_repo.search, query=query, limit=10, filter_expr=self.filter_expr()
            )
        except Exception as e:
            logger.error(f"Vector检索失败,查询={query} 原因={str(e)}")
            return []
        return map_vector_record(query, search_results)

    def filter_expr(self) -> str:
        """生成按发布时间过滤的 Milvus 表达式。"""
        days = get_settings().INSIGHT_VECTOR_FILTER_DAYS
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        return f"published_at >= {start_ts}"

    async def _retrival_db_evidence(
        self, retrival_db_tasks: list[RetrievalQueryTask]
    ) -> list[EvidenceRecord]:
        """并发执行多通道 MySQL 召回并聚合证据。"""
        task_responses = await asyncio.gather(
            *[self._run_retrival_db_evidence(task) for task in retrival_db_tasks]
        )
        final_search_results: list[EvidenceRecord] = []
        for retrival_task, response in zip(retrival_db_tasks, task_responses):
            final_search_results.extend(map_db_record(retrival_task, response))
        return final_search_results

    async def _run_retrival_db_evidence(self, task: RetrievalQueryTask) -> Optional[SearchResponse]:
        """按通道分发执行单条 MySQL 召回任务。"""
        db_repo = self._db_repo
        match task.channel:
            case "keyword_recall":
                return await db_repo.keyword_recall(task.query, limit=task.limit)
            case "comment_recall":
                return await db_repo.comment_recall(task.query, limit=task.limit)
            case "hot_recall":
                return await db_repo.hot_recall(time_period="year", limit=task.limit)
            case _:
                logger.error(f"通道 {task.channel} 未知...")
                return None


def map_db_record(
    retrival_task: RetrievalQueryTask, response: SearchResponse
) -> list[EvidenceRecord]:
    """将 MySQL 召回响应批量转换为证据记录。"""
    return [_map_to_db_record(retrival_task, record) for record in response.search_results]


def _map_to_db_record(retrival_task: RetrievalQueryTask, record: SearchRecord) -> EvidenceRecord:
    """将 MySQL 记录转为 EvidenceRecord。"""
    return EvidenceRecord(
        id=record.mysql_pk,
        platform=record.platform,
        source_table=record.source_table,
        source_keyword=record.source_keyword,
        content=record.title_or_content,
        published_at=record.published_at.strftime("%Y-%m-%d %H:%M:%S"),
        hotness_score=record.hotness_score,
        engagement=Engagement(
            likes=record.engagement.get("likes", 0),
            comments=record.engagement.get("comments", 0),
            shares=record.engagement.get("shares", 0),
            collects=record.engagement.get("collects", 0),
            replies=record.engagement.get("replies", 0),
        ),
        retrieval=RetrievalMeta(
            matched_queries=[retrival_task.query],
            retrieval_channels=[retrival_task.channel],
            retrieval_scores={retrival_task.channel: retrival_task.channel_score},
        ),
    )


def map_vector_record(query: str, search_results: list[SearchHit]) -> list[EvidenceRecord]:
    """将 Milvus 检索命中批量转换为证据记录。"""
    return [_map_to_vector_record(query, result) for result in search_results]


def _map_to_vector_record(query: str, result: SearchHit) -> EvidenceRecord:
    """将 Milvus 命中转为 EvidenceRecord。"""
    doc = result.retrieval_doc
    return EvidenceRecord(
        id=doc.doc_id,
        platform=doc.platform,
        source_table=doc.source_table,
        source_keyword=doc.source_keyword,
        content=doc.content,
        published_at=doc.published_at.strftime("%Y-%m-%d %H:%M:%S"),
        hotness_score=doc.hotness_score,
        engagement=Engagement(
            likes=doc.likes,
            comments=doc.comments,
            shares=doc.shares,
            collects=doc.collects,
            replies=doc.replies,
        ),
        retrieval=RetrievalMeta(
            matched_queries=[query],
            retrieval_channels=[result.retrieval_channel],
            retrieval_scores={result.retrieval_channel: result.retrieval_score},
        ),
    )
