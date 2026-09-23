from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from engines.common.llm.llm_client import LLMClient


@dataclass(frozen=True)
class ProgressUpdate:
    """节点进度更新载荷(状态/消息/百分比)"""

    status: str
    message: str
    progress_pct: int


@runtime_checkable
class ResearchNodeContext(Protocol):
    """研究节点运行时上下文协议"""

    llm_client: LLMClient
    output_dir: str

    def report_progress(self, status: str, message: str, pct: int) -> None:
        """上报当前节点执行进度"""
        pass


class BaseNode(ABC):
    """LangGraph 节点抽象基类"""

    def __init__(self, context: ResearchNodeContext) -> None:
        """注入运行时上下文构造节点"""
        self.context = context

    @abstractmethod
    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """节点执行入口(子类实现)"""
        pass
