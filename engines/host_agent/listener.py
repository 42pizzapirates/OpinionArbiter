import asyncio
from typing import Any

from loguru import logger

from engines.common.eventing.bus import subscribe, unsubscribe
from engines.common.eventing.event import EventType
from engines.common.eventing.publishers import publish_host_discussion_message
from engines.contracts.roles import role_display_name
from engines.host_agent.graph import build_graph
from engines.host_agent.judge import Judge
from engines.host_agent.state import Session


class SectionReadyListener:
    """监听章节就绪事件,串行驱动主持人研判图。"""

    def __init__(self) -> None:
        """构建主持人、研判图、会话与异步队列工作器。"""
        judge = Judge()
        self.session = Session()
        self.graph = build_graph(judge)
        self._queue: asyncio.Queue[dict[str, Any]] | None = None
        self._worker: asyncio.Task | None = None

    def start(self) -> None:
        """幂等启动事件订阅与后台 worker。"""
        if self._worker is not None:
            return
        self._queue = asyncio.Queue()
        subscribe(EventType.SECTION_READY, self._on_callback)
        self._worker = asyncio.create_task(self._run())
        logger.info("SectionReadyListener: 启动, 按章节维度进行主持人研判")

    def stop(self) -> None:
        """停止事件订阅 + 取消 worker"""
        if self._worker is None:
            return
        unsubscribe(self._on_callback)
        self._worker.cancel()
        self._worker = None
        self._queue = None
        self.session.clear()
        logger.info("SectionReadyListener: 已停止")

    def _on_callback(self, _event_type: EventType, payload_data: dict) -> None:
        """将事件载荷入队等待 worker 串行消费。"""
        self._queue.put_nowait(payload_data)

    async def _run(self) -> None:
        """自旋消费队列,驱动研判图并发布主持人讨论消息。"""
        host_name = role_display_name("host")
        while True:
            section_pack = await self._queue.get()
            try:
                state = self.session.to_state(section_pack)
                final_state = await self.graph.ainvoke(state)
                self.session.apply_state(final_state)
                discussion_messages = final_state.get("outbox")
            except Exception as exc:
                logger.exception(f"SectionReadyListener: 章节发现处理失败: {exc}")
                continue
            for discussion_message in discussion_messages:
                logger.info(
                    f"【{host_name}】发送讨论消息:"
                    f"来源={role_display_name(discussion_message.source):<12} | "
                    f"章节={discussion_message.section_key:<10} | "
                    f"内容={discussion_message.content[:20]}..."
                )
                publish_host_discussion_message(discussion_message)
