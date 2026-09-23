from pydantic import BaseModel, Field


class HostStateResponse(BaseModel):
    """主持人运行状态响应体。"""

    host_running: bool


class HostDiscussionRecord(BaseModel):
    """主持人讨论区单条发言记录。"""

    source: str = ""
    message_text: str = ""
    sent_at: str = ""
    dimension_key: str = ""


class HostDiscussionRecordsResponse(BaseModel):
    """主持人讨论区发言记录列表响应。"""

    discussion_records: list[HostDiscussionRecord] = Field(default_factory=list)
