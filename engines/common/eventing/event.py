from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """事件总线的事件类型枚举"""

    ROLE_PROGRESS = "role_progress"
    ROLE_ERROR = "role_error"
    ROLE_RESULT = "role_result"
    SECTION_READY = "section_ready"
    HOST_DISCUSSION_MESSAGE = "host_discussion_message"


class RoleProgressEvent(BaseModel):
    """角色执行进度事件(状态/消息/百分比)"""

    role: str
    status: str
    message: str = ""
    progress_pct: int = 0


class RoleResultEvent(BaseModel):
    """角色执行完成事件"""

    role: str


class RoleErrorEvent(BaseModel):
    """角色执行异常事件"""

    role: str
    error: str


class SectionReadyEvent(BaseModel):
    """章节内容就绪事件(供编排消费)"""

    source: str
    agent_name: str
    section_key: str
    section_index: int
    title: str = ""
    query: str = ""
    body: str = ""
    section_metadata: dict[str, Any] = Field(default_factory=dict)


class HostDiscussionMessageEvent(BaseModel):
    """主持研判讨论消息事件"""

    type: Literal["agent", "host"] = "agent"
    source: Literal["insight", "media", "host"]
    content: str
    timestamp: str = ""
    section_key: str = ""
