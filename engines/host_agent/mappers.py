from datetime import datetime

from engines.common.eventing.event import HostDiscussionMessageEvent
from engines.host_agent.schemas import SectionJudgement, SectionResult


def build_agent_event(result: SectionResult) -> HostDiscussionMessageEvent:
    """构造 Agent(insight/media)章节发言事件。"""
    return HostDiscussionMessageEvent(
        type="agent",
        source=result.source,  # type: ignore
        content=result.body[:2000],
        section_key=result.section_key,
        timestamp=_now_time(),
    )


def build_judgement_event(judgement: SectionJudgement) -> HostDiscussionMessageEvent:
    """构造主持人单维度阶段裁判事件。"""
    return HostDiscussionMessageEvent(
        type="host",
        source="host",
        content=judgement.content,
        section_key=judgement.section_key,
        timestamp=_now_time(),
    )


def build_final_event(content: str) -> HostDiscussionMessageEvent:
    """构造主持人最终裁判事件(无维度)。"""
    return HostDiscussionMessageEvent(
        type="host",
        source="host",
        content=content,
        section_key="",
        timestamp=_now_time(),
    )


def append_event(
        outbox: list[HostDiscussionMessageEvent],
        event: HostDiscussionMessageEvent,
) -> list[HostDiscussionMessageEvent]:
    """返回追加了新事件的 outbox"""
    return [*outbox, event]


def _now_time() -> str:
    """返回当前时分秒字符串,用于事件时间戳。"""
    return datetime.now().strftime("%H:%M:%S")
