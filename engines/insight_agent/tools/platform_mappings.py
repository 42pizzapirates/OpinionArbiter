from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class ContentTableMapping:
    """内容表的字段与互动列映射配置。"""

    table_name: str

    text_col: str

    published_at_col: str

    source_keyword_col: str

    engagement_cols: Mapping[str, str]

    search_fields: tuple[str, ...]


@dataclass
class CommentTableMapping:
    """评论表的字段与互动列映射配置。"""

    table_name: str

    text_col: str

    published_at_col: str

    engagement_cols: Mapping[str, str]

    search_fields: tuple[str, ...]


@dataclass
class PlatformSearchMapping:
    """平台内容表与评论表的统一映射配置。"""

    platform_name: str

    content_mapping: ContentTableMapping

    comment_mapping: CommentTableMapping


PLATFORM_MAPPING: dict[str, Any] = {
    "douyin": PlatformSearchMapping(
        platform_name="douyin",
        content_mapping=ContentTableMapping(
            table_name="douyin_aweme",
            text_col="title",
            published_at_col="create_time",
            source_keyword_col="source_keyword",
            engagement_cols={
                "likes": "liked_count",
                "comments": "comment_count",
                "shares": "share_count",
                "collects": "collected_count",
            },
            search_fields=("title", "source_keyword"),
        ),
        comment_mapping=CommentTableMapping(
            table_name="douyin_aweme_comment",
            text_col="content",
            published_at_col="create_time",
            engagement_cols={
                "likes": "like_count",
                "replies": "sub_comment_count",
            },
            search_fields=("content",),
        ),
    ),
    "weibo": PlatformSearchMapping(
        platform_name="weibo",
        content_mapping=ContentTableMapping(
            table_name="weibo_note",
            text_col="content",
            published_at_col="create_time",
            source_keyword_col="source_keyword",
            engagement_cols={
                "likes": "liked_count",
                "comments": "comments_count",
                "shares": "shared_count",
            },
            search_fields=("content", "source_keyword"),
        ),
        comment_mapping=CommentTableMapping(
            table_name="weibo_note_comment",
            text_col="content",
            published_at_col="create_time",
            engagement_cols={
                "likes": "comment_like_count",
                "replies": "sub_comment_count",
            },
            search_fields=("content",),
        ),
    ),
}
