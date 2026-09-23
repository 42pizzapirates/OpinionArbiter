from typing import Callable

from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate


class InsightContext:
    """私域舆情智能体共享上下文：角色、LLM 与进度回调。"""

    def __init__(
            self,
            role: str,
            llm_client: LLMClient,
            output_dir: str,
            progress_callback: Callable[[ProgressUpdate], None] | None,
    ) -> None:
        """注入角色、LLM 客户端、输出目录与进度回调。"""
        self.role = role
        self.llm_client = llm_client
        self.output_dir = output_dir
        self.progress_callback = progress_callback

    def report_progress(self, status: str, message: str, pct: int) -> None:
        """向上报研究阶段进度与百分比。"""
        self.progress_callback(ProgressUpdate(status, message, pct))
