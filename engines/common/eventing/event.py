"""
事件类型
事件数据
"""

from pydantic import  BaseModel
from enum import Enum


class EventType(str, Enum):
    ROLE_PROGRESS = "role_progress"
    ROLE_ERROR = "role_error"
    ROLE_RESULT = "role_result"
    SECTION_READY = "section_ready"   # 后续两个子Agent发送给主持人Agent使用的事件类型
    HOST_DISCUSSION_MESSAGE = "host_discussion_message"

class RoleProgressEvent(BaseModel):
    role: str               # Agent角色
    status: str             # 节点的阶段
    message: str = ""       # 展示进度的文案
    progress_pct: int = 0   # 展示进度的百分比

class RoleResultEvent(BaseModel):
    role: str               # Agent角色

class RoleErrorEvent(BaseModel):
    role: str               # Agent角色
    error: str              # 错误原因





