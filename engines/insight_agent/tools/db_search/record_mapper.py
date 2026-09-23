from typing import Any

from engines.insight_agent.tools.db_search.search_results import SearchRecord
from engines.insight_agent.tools.platform_mappings import PLATFORM_MAPPING
from engines.insight_agent.tools.utils import (
    extract_engagement,
    to_datetime,
    to_unique_id,
)


def db_row_to_search_record(result_row: dict[str, Any]) -> SearchRecord:
    """按平台映射将数据库行转为检索记录。"""
    platform_name = result_row.get("platform")
    platform_mapping = PLATFORM_MAPPING.get(platform_name)
    table_name = platform_mapping.comment_mapping.table_name
    is_comment = result_row.get("source_table") == table_name
    platform_mapping = (
        platform_mapping.comment_mapping if is_comment else platform_mapping.content_mapping
    )
    return SearchRecord(
        platform=result_row.get("platform"),
        source_table=result_row.get("source_table"),
        mysql_pk=to_unique_id(platform_name, table_name, result_row.get("mysql_pk")),
        title_or_content=result_row.get("title"),
        published_at=to_datetime(result_row.get("published_at")),
        source_keyword=result_row.get("source_keyword"),
        engagement=extract_engagement(result_row, platform_mapping),
        hotness_score=result_row.get("hotness_score"),
    )
