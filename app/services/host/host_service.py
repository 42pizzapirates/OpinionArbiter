from loguru import logger
from typing import Any, Optional

from engines.common.eventing.bus import subscribe, unsubscribe
from engines.common.eventing.event import EventType
from engines.contracts.roles import role_display_name
from engines.host_agent.listener import SectionReadyListener
from app.services.host.discuss_buffer import DiscussionBuffer


class HostService:

    def __init__(self):
        self._listener: Optional[SectionReadyListener] = None
        self.discussion_buffer = DiscussionBuffer()

    def register_discussion_buffer(self):
        subscribe(EventType.HOST_DISCUSSION_MESSAGE, self._on_discussion_message)

    def _on_discussion_message(self, _event_type: EventType, data: dict[str, Any]) -> None:
        # 提取关键信息
        source = data.get("source")
        section_key = data.get("section_key")
        content = data.get("content")
        self.discussion_buffer.append_message(data)
        host_name = role_display_name("host")
        logger.info(
            f"【{host_name}】收到讨论消息 | "
            f"来源={role_display_name(source):<12} | "
            f"章节={section_key:<10} | "
            f"内容={content[:20]}..."
        )

    def stop_discussion_buffer(self):
        unsubscribe(self._on_discussion_message)

    def start_host(self):
        if self._listener is not None:
            return True
        try:
            self._listener = SectionReadyListener()
            self._listener.start()
            logger.info("HostService: 研判引擎启动成功")
            return True
        except Exception as exc:
            logger.exception(f"HostService: 启动研判引擎失败: {exc}")
            self._listener = None
            return False

    def stop_host(self):
        if self._listener is None:
            return
        try:
            self._listener.stop()
            logger.info("HostService: 研判引擎已停止")
        except Exception as exc:
            logger.exception(f"HostService: 停止研判引擎失败: {exc}")
        finally:
            self._listener = None

    def get_discussion_records(self):
        return self.discussion_buffer.read_messages()
