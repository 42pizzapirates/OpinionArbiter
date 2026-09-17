from dataclasses import dataclass
from enum import Enum
import time
from typing import Optional


class ReportTaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ReportTask:
    task_id: str
    status: ReportTaskStatus = ReportTaskStatus.RUNNING
    html_content: str = ""
    report_file_path: str = ""
    report_file_name: str = ""
    markdown_file_path: str = ""
    markdown_file_name: str = ""

    def update_status(self, status: ReportTaskStatus) -> None:
        self.status = status


class ReportTaskStore:

    def __init__(self) -> None:
        self.current_task: Optional[ReportTask] = None
        self.tasks_registry: dict[str, ReportTask] = {}

    def create_generate_task(self) -> ReportTask:
        if self.current_task and self.current_task.status == ReportTaskStatus.RUNNING:
            raise RuntimeError("已有报告生成任务在运行中")
        if self.current_task and self.current_task.status in (
                ReportTaskStatus.COMPLETED,
                ReportTaskStatus.ERROR,
        ):
            self.current_task = None

        task = ReportTask(f"report_{int(time.time())}")
        self.current_task = task
        self.tasks_registry[task.task_id] = task
        return task

    def get_generate_task(self, task_id: str) -> Optional[ReportTask]:
        return self.tasks_registry.get(task_id)
