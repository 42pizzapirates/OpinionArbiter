"""SSE 广播器：订阅研究角色事件并转发给 SSE 客户端。"""

import asyncio
import json

from loguru import logger

from engines.common.eventing.event import EventType
from engines.common.eventing.bus import subscribe, unsubscribe


class SseBroadcaster:
    """订阅角色进度、结果与错误事件，并向在线的 SSE 客户端实时广播。"""

    ALLOWED_EVENT_TYPES = (EventType.ROLE_PROGRESS, EventType.ROLE_RESULT, EventType.ROLE_ERROR)

    def __init__(self) -> None:
        """初始化广播器，构建订阅者队列池。"""

        self._subscribers: list[asyncio.Queue] = []

    def start(self) -> None:
        """向全局事件总线注册订阅监听。"""

        for event_type in self.ALLOWED_EVENT_TYPES:
            subscribe(event_type, self.forward_event)

    def stop(self) -> None:
        """注销事件监听并清空订阅者。"""

        unsubscribe(self.forward_event)
        self._subscribers.clear()

    def forward_event(self, event_type: EventType, data: dict) -> None:
        """将事件总线消息序列化后广播给当前在线的所有客户端。"""

        payload = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)

        for queue in list(self._subscribers):
            queue.put_nowait(payload)

    async def stream_events(self, request):
        """处理 SSE 客户端连接生命周期并推送实时事件。"""

        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        logger.debug("SSE client connected")

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
            logger.debug("SSE client disconnected")
