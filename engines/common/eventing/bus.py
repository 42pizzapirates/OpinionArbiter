from typing import Any, Callable

from loguru import logger

from engines.common.eventing.event import EventType

EventCallback = Callable[[EventType, dict[str, Any]], None]
_subscribers: dict[EventType, set[EventCallback]] = {}


def subscribe(event_type: EventType, callback: EventCallback):
    """订阅指定事件类型的回调"""
    _subscribers.setdefault(event_type, set()).add(callback)


def publish(event_type: EventType, data: dict[str, Any]) -> None:
    """向该事件所有订阅者广播数据"""
    for callback in list(_subscribers.get(event_type, ())):
        try:
            callback(event_type, data)
        except Exception as exc:
            logger.error(f"订阅者订阅失败原因：{str(exc)}")


def unsubscribe(callback: EventCallback) -> None:
    """从全部事件类型中移除指定回调"""
    for subs in _subscribers.values():
        subs.discard(callback)


def clear():
    """清空所有事件类型与订阅者"""
    _subscribers.clear()
