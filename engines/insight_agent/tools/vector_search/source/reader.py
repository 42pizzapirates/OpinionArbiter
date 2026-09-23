from typing import Any

from sqlalchemy import column, select, table

from engines.insight_agent.tools.connection import get_session_factory
from engines.insight_agent.tools.db_search.queries.columns import (
    hot_score_metric_column,
    safe_number_column,
)
from engines.insight_agent.tools.platform_mappings import (
    PLATFORM_MAPPING,
    CommentTableMapping,
    ContentTableMapping,
)
from engines.insight_agent.tools.utils import extract_engagement, to_unique_id
from engines.insight_agent.tools.vector_search.search_results import VectorDocument


class SourceDocumentReader:
    """从 MySQL 读取全量文档用于知识库同步。"""

    def __init__(self) -> None:
        """绑定会话工厂与平台映射表。"""
        self.mappings = PLATFORM_MAPPING

    async def get_all_documents(self) -> list[VectorDocument]:
        """获取所有平台内容表和评论表的全量向量文档数据。"""
        all_documents: list[VectorDocument] = []
        for platform, config in self.mappings.items():
            if config.content_mapping:
                all_documents.extend(await self._get_table_data(config.content_mapping, platform))
            if config.comment_mapping:
                all_documents.extend(await self._get_table_data(config.comment_mapping, platform))
        return all_documents

    async def _get_table_data(
            self, config: ContentTableMapping | CommentTableMapping, platform: str
    ) -> list[VectorDocument]:
        """查询单表并转为向量文档且过滤空内容。"""
        stmt = _build_select_query(config)
        async with get_session_factory() as session:
            result = await session.execute(stmt)
            rows = result.mappings().all()
        raw_docs = [_row_to_document(dict(row), config, platform) for row in rows]
        return [doc for doc in raw_docs if doc.content.strip()]


def _build_select_query(table_mapping: ContentTableMapping | CommentTableMapping) -> Any:
    """构建带互动指标与热度的单表查询。"""
    tbl = table(table_mapping.table_name)
    columns = [
        column("id").label("id"),
        column(table_mapping.text_col).label("text_content"),
        column(table_mapping.published_at_col).label("published_ts"),
    ]
    source_keyword_col = getattr(table_mapping, "source_keyword_col", None)
    if source_keyword_col:
        columns.append(column(source_keyword_col).label("source_keyword"))
    for metric, col_name in table_mapping.engagement_cols.items():
        columns.append(safe_number_column(col_name).label(f"eng_{metric}"))
    columns.append(hot_score_metric_column(table_mapping))
    return select(*columns).select_from(tbl).order_by(column("id"))


def _row_to_document(
        result_row: dict[str, Any],
        table_mapping: ContentTableMapping | CommentTableMapping,
        platform_name: str,
) -> VectorDocument:
    """将单行结果转为跨平台向量文档。"""
    return VectorDocument(
        doc_id=to_unique_id(platform_name, table_mapping.table_name, result_row.get("id")),
        platform=platform_name,
        source_table=table_mapping.table_name,
        mysql_pk=result_row.get("id"),
        content=result_row.get("text_content"),
        published_at=result_row.get("published_ts"),
        source_keyword=result_row.get("source_keyword"),
        hotness_score=result_row.get("hotness_score"),
        **extract_engagement(result_row, table_mapping),
    )
