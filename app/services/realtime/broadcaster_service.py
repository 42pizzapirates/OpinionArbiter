"""SSE 广播器:订阅研究角色事件,转发给 SSE 客户端。"""
import asyncio
import json
from loguru import logger
from engines.common.eventing.event import EventType
from engines.common.eventing.bus import subscribe, unsubscribe


class BroadcasterService:
    """订阅角色进度/结果/错误事件，并向所有在线的 SSE 客户端进行纯实时广播。"""

    FORWARDED_EVENT_TYPES = (EventType.ROLE_PROGRESS, EventType.ROLE_RESULT, EventType.ROLE_ERROR)

    def __init__(self) -> None:
        """初始化广播器，构建订阅者队列池。"""

        self._subscribers: list[asyncio.Queue] = []

    def register_broadcaster(self) -> None:
        """启动广播器，向全局事件总线注册订阅监听"""

        for event_type in self.FORWARDED_EVENT_TYPES:
            subscribe(event_type, self.forward_event)

    def stop_broadcaster(self) -> None:
        """停止广播器，注销事件监听并清空订阅者"""

        unsubscribe(self.forward_event)
        self._subscribers.clear()

    def forward_event(self, event_type: EventType, data: dict) -> None:
        """接收事件总线的原生事件，序列化后直接广播给当前在线的所有客户端。"""

        payload = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)

        for queue in list(self._subscribers):
            queue.put_nowait(payload)

    async def stream_research_progress(self, request):
        """异步生成器：处理 SSE 客户端连接生命周期，仅进行实时事件推送。"""

        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        logger.debug("SSE 客户端连接")

        try:
            yield {"event": "connected", "data": json.dumps({"status": "connected"})}

            while True:
                if await request.is_disconnected():
                    break
                payload = await queue.get()
                yield {"data": payload}
        finally:

            if queue in self._subscribers:
                self._subscribers.remove(queue)
            logger.debug("SSE 客户端关闭")
