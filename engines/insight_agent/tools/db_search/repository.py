from typing import Any, Callable

from loguru import logger
from sqlalchemy import column, desc, union_all

from engines.insight_agent.tools.connection import get_async_engine
from engines.insight_agent.tools.db_search.queries.builder import (
    build_comment_search_query,
    build_content_search_query,
    build_hotness_query,
)
from engines.insight_agent.tools.db_search.record_mapper import db_row_to_search_record
from engines.insight_agent.tools.db_search.search_results import (
    SearchRecord,
    SearchResponse,
)
from engines.insight_agent.tools.hotness import HotRecallPeriod
from engines.insight_agent.tools.platform_mappings import PLATFORM_MAPPING

RecordMapper = Callable[[dict[str, Any]], SearchRecord]


class DatabaseSearchRepository:
    """MySQL 跨平台三通道召回仓储。"""

    async def hot_recall(
            self, time_period: HotRecallPeriod = "week", limit: int = 20
    ) -> SearchResponse:
        """根据时间周期进行跨平台的全网热度数据召回。"""
        select_queries = [
            build_hotness_query(platform_mapping, time_period, limit)
            for platform_mapping in PLATFORM_MAPPING.values()
        ]
        statement = union_all(*select_queries).order_by(desc(column("hotness_score"))).limit(limit)
        return await self._execute_search(
            channel="hot_recall",
            statement=statement,
            record_mapper=db_row_to_search_record,
        )

    async def keyword_recall(self, topic_keyword: str, limit: int = 20) -> SearchResponse:
        """根据主题关键词进行跨平台的内容匹配召回。"""
        search_term = f"%{topic_keyword}%"
        select_queries = [
            build_content_search_query(platform_mapping, search_term, limit)
            for platform_mapping in PLATFORM_MAPPING.values()
        ]
        statement = union_all(*select_queries).order_by(desc(column("published_at")))
        return await self._execute_search(
            channel="keyword_recall",
            statement=statement,
            record_mapper=db_row_to_search_record,
        )

    async def comment_recall(self, comment_keyword: str, limit: int = 60) -> SearchResponse:
        """根据关键词进行跨平台的评论与舆情观点数据召回。"""
        search_term = f"%{comment_keyword}%"
        select_queries = [
            build_comment_search_query(adapter, search_term, limit)
            for adapter in PLATFORM_MAPPING.values()
        ]
        statement = union_all(*select_queries).order_by(desc(column("published_at"))).limit(limit)
        return await self._execute_search(
            channel="comment_recall",
            statement=statement,
            record_mapper=db_row_to_search_record,
        )

    async def _execute_search(
            self,
            *,
            channel: str,
            statement: Any,
            record_mapper: RecordMapper,
    ) -> SearchResponse:
        """执行 SQL 并封装为带通道与错误信息的响应。"""
        rows = []
        error_message = None
        try:
            rows = await self._fetch_rows(statement)
        except Exception as e:
            error_message = str(e)
            logger.exception(f"数据库查询时发生错误: {error_message}")
        records = self._map_rows(rows, record_mapper)
        return SearchResponse(
            retrieval_channel=channel,
            search_results=records,
            search_results_count=len(records),
            search_error_message=error_message,
        )

    @staticmethod
    async def _fetch_rows(select_statement) -> list[dict[str, Any]]:
        """执行 SQL 并返回字典列表"""
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(select_statement)
            rows = result.mappings().all()
            return [dict(row) for row in rows]

    @staticmethod
    def _map_rows(rows: list[dict[str, Any]], row_mapper: RecordMapper) -> list[SearchRecord]:
        """按映射函数将结果行批量转为检索记录。"""
        records: list[SearchRecord] = []
        for row in rows:
            records.append(row_mapper(row))
        return records
