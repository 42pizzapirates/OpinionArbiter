from typing import Mapping, cast

from sqlalchemy import DECIMAL, cast as sa_cast, column, func, literal, literal_column
from sqlalchemy.sql.elements import ColumnElement

from engines.insight_agent.tools.hotness import ENGAGEMENT_METRICS, HotScoreWeights
from engines.insight_agent.tools.platform_mappings import (
    CommentTableMapping,
    ContentTableMapping,
    PlatformSearchMapping,
)


def content_search_columns(platform_mapping: PlatformSearchMapping) -> list[ColumnElement]:
    """生成内容表检索所需的标准列定义列表。"""
    content_mapping = platform_mapping.content_mapping
    return [
        literal(platform_mapping.platform_name).label("platform"),
        literal(content_mapping.table_name).label("source_table"),
        column("id").label("mysql_pk"),
        column(content_mapping.text_col).label("title"),
        column(content_mapping.published_at_col).label("published_at"),
        column(content_mapping.source_keyword_col).label("source_keyword"),
    ]


def comment_search_columns(platform_mapping: PlatformSearchMapping) -> list[ColumnElement]:
    """生成评论表检索所需的标准列定义列表。"""
    comment_mapping = platform_mapping.comment_mapping
    return [
        literal(platform_mapping.platform_name).label("platform"),
        literal(comment_mapping.table_name).label("source_table"),
        column("id").label("mysql_pk"),
        column(comment_mapping.text_col).label("title"),
        column(comment_mapping.published_at_col).label("published_at"),
        literal_column("NULL").label("source_keyword"),
    ]


def engagement_metric_columns(engagement_column_map: Mapping[str, str]) -> list[ColumnElement]:
    """根据互动指标映射构建带统一前缀的互动数据列列表。"""
    result_columns = []
    for engagement_metric in ENGAGEMENT_METRICS:
        if engagement_metric in engagement_column_map:
            mapped_column = engagement_column_map[engagement_metric]
            base_column = safe_number_column(mapped_column)
        else:
            base_column = literal_column("0")
        labeled_column = base_column.label(f"eng_{engagement_metric}")
        result_columns.append(labeled_column)
    return result_columns


def hot_score_metric_column(
    table_mapping: ContentTableMapping | CommentTableMapping,
) -> ColumnElement:
    """根据指标权重构建加权计算热度得分的列定义。"""
    hotness_expression = None
    metric_weights = HotScoreWeights()
    for metric_key, db_column_name in table_mapping.engagement_cols.items():
        current_weight = getattr(metric_weights, metric_key)
        weighted_metric_term = safe_number_column(db_column_name) * current_weight
        if hotness_expression is None:
            hotness_expression = weighted_metric_term
        else:
            hotness_expression = hotness_expression + weighted_metric_term
    return cast(ColumnElement, hotness_expression).label("hotness_score")


def safe_number_column(col_name: str) -> ColumnElement:
    """将列转换为数字类型并处理 NULL 值，确保数值计算安全。"""
    return func.coalesce(sa_cast(column(col_name), DECIMAL), 0.0)
