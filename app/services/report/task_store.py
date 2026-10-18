from dataclasses import dataclass
from enum import Enum
import time
from typing import Optional
from engines.report_engine.engine import ReportOutput


class ReportTaskStatus(str, Enum):
    """综合报告任务状态枚举"""
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ReportTask:
    """综合报告生成任务的数据载体"""

    task_id: str
    html_content: str = ""
    report_file_path: str = ""
    report_file_name: str = ""
    markdown_file_path: str = ""
    markdown_file_name: str = ""
    status: ReportTaskStatus = ReportTaskStatus.RUNNING

    def complete_task(self, report_out: ReportOutput) -> None:
        """使用生成的综合报告结果更新任务状态并标记完成。"""

        self.html_content = report_out.html_content
        self.report_file_path = report_out.report_filepath
        self.report_file_name = report_out.report_filename

        self.markdown_file_path = report_out.markdown_filepath
        self.markdown_file_name = report_out.markdown_filename

        self.status = ReportTaskStatus.COMPLETED


class ReportTaskStore:
    """在内存中管理和维护报告任务的存储器"""

    def __init__(self) -> None:
        """初始化任务存储器，设置内存缓存"""

        self.current_task: Optional[ReportTask] = None

        self.tasks_registry: dict[str, ReportTask] = {}

    def create_generate_task(self) -> ReportTask:
        """创建并注册一个新的报告生成任务。"""

        if self.current_task and self.current_task.status == ReportTaskStatus.RUNNING:
            raise RuntimeError("已有报告生成任务在运行中")

        if self.current_task and self.current_task.status in (
                ReportTaskStatus.COMPLETED,
                ReportTaskStatus.ERROR,
        ):
            self.current_task = None

        task = ReportTask(task_id=f"report_{int(time.time())}")

        self.current_task = task
        self.tasks_registry[task.task_id] = task
        return task

    def get_generate_task(self, task_id: str) -> Optional[ReportTask]:
        """根据任务 ID 获取注册表中的任务详情。"""

        return self.tasks_registry.get(task_id)
