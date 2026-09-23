from engines.common.eventing.bus import publish
from engines.common.eventing.event import (
    EventType,
    HostDiscussionMessageEvent,
    RoleErrorEvent,
    RoleProgressEvent,
    RoleResultEvent,
    SectionReadyEvent,
)


def pub_role_progress(data: RoleProgressEvent):
    """发布角色进度事件到事件总线"""
    publish(event_type=EventType.ROLE_PROGRESS, data=data.model_dump())


def pub_role_result(data: RoleResultEvent):
    """发布角色完成事件到事件总线"""
    publish(event_type=EventType.ROLE_RESULT, data=data.model_dump())


def pub_role_error(data: RoleErrorEvent):
    """发布角色异常事件到事件总线"""
    publish(event_type=EventType.ROLE_ERROR, data=data.model_dump())


def publish_section_read_ready(event: SectionReadyEvent) -> None:
    """发布章节就绪事件到事件总线"""
    publish(EventType.SECTION_READY, event.model_dump())


def publish_host_discussion_message(event: HostDiscussionMessageEvent) -> None:
    """发布主持研判讨论消息事件到事件总线"""
    publish(EventType.HOST_DISCUSSION_MESSAGE, event.model_dump())
