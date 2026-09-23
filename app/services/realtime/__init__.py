"""SSE 广播器:订阅研究角色事件,转发给 SSE 客户端。"""

import asyncio
import json

from loguru import logger

from engines.common.eventing.event import EventType
from engines.common.eventing.bus import subscribe, unsubscribe


class SseBroadcaster:
    """订阅角色进度/结果/错误事件，并向所有在线的 SSE 客户端进行实时广播"""

    # 允许转发的事件类型白名单
    ALLOWED_EVENT_TYPES = (EventType.ROLE_PROGRESS, EventType.ROLE_RESULT, EventType.ROLE_ERROR)

    def __init__(self) -> None:
        """初始化广播器，构建订阅者队列池。"""

        # 1. 存储所有活跃客户端的异步事件队列列表
        self._subscribers: list[asyncio.Queue] = []

    def start(self) -> None:
        """启动广播器，向全局事件总线注册订阅监听。"""

        # 1. 遍历关注的事件类型，将转发方法绑定到事件上
        for event_type in self.ALLOWED_EVENT_TYPES:
            subscribe(event_type, self.forward_event)

    def stop(self) -> None:
        """停止广播器，注销事件监听并清空订阅者。"""

        # 1. 从事件中心注销当前转发函数
        unsubscribe(self.forward_event)

        # 2. 清空所有客户端队列以释放连接
        self._subscribers.clear()

    def forward_event(self, event_type: EventType, data: dict) -> None:
        """接收事件总线的原生事件，序列化后直接广播给当前在线的所有客户端。"""
        # 1. 将原生事件字典序列化为 JSON 字符串
        payload = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)

        # 2. 遍历并直接推送到所有活跃的客户端队列中
        for queue in list(self._subscribers):
            queue.put_nowait(payload)

    async def stream_events(self, request):
        """异步生成器：处理 SSE 客户端连接生命周期，仅进行实时事件推送。"""

        # 1. 为当前新连接创建一个专属的异步队列
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        logger.debug("SSE client connected")

        try:
            # 2. 首先向客户端推送连接成功消息
            yield {"event": "connected", "data": json.dumps({"status": "connected"})}

            # 3. 一直等待并消费队列中由 forward_event 放入入的实时新事件
            while True:
                if await request.is_disconnected():
                    break
                payload = await queue.get()
                yield {"data": payload}
        finally:
            # 4. 客户端断开连接时，将其移出订阅池释放队列资源
            if queue in self._subscribers:
                self._subscribers.remove(queue)
            logger.debug("SSE client disconnected")
