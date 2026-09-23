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

    task_id: str  # 任务唯一标识符（基于时间戳生成）
    html_content: str = ""  # 生成的 HTML 报告文本内容
    report_file_path: str = ""  # HTML 报告在磁盘上的绝对路径
    report_file_name: str = ""  # HTML 报告的文件名
    markdown_file_path: str = ""  # Markdown 报告在磁盘上的绝对路径
    markdown_file_name: str = ""  # Markdown 报告的文件名
    status: ReportTaskStatus = ReportTaskStatus.RUNNING  # 任务当前的执行状态（默认为运行中）

    def complete_task(self, report_out: ReportOutput) -> None:
        """使用生成的综合报告结果更新任务状态并标记完成。"""

        # 1. 填充 HTML 报告的内容与落盘文件元数据
        self.html_content = report_out.html_content
        self.report_file_path = report_out.report_filepath
        self.report_file_name = report_out.report_filename

        # 2. 填充 Markdown 报告的落盘文件元数据
        self.markdown_file_path = report_out.markdown_filepath
        self.markdown_file_name = report_out.markdown_filename

        # 3. 将任务状态变更为已完成
        self.status = ReportTaskStatus.COMPLETED


class ReportTaskStore:
    """在内存中管理和维护报告任务的存储器"""

    def __init__(self) -> None:
        """初始化任务存储器，设置内存缓存"""

        # 1. 初始化当前正在运行的单个任务缓存
        self.current_task: Optional[ReportTask] = None

        # 2. 初始化所有历史任务的注册表字典
        self.tasks_registry: dict[str, ReportTask] = {}

    def create_generate_task(self) -> ReportTask:
        """创建并注册一个新的报告生成任务。"""

        # 1. 若当前已有任务正在运行，则拒绝创建新任务以防冲突
        if self.current_task and self.current_task.status == ReportTaskStatus.RUNNING:
            raise RuntimeError("已有报告生成任务在运行中")

        # 2. 若当前任务槽中存在已结束的任务，则将其释放
        if self.current_task and self.current_task.status in (
                ReportTaskStatus.COMPLETED,
                ReportTaskStatus.ERROR,
        ):
            self.current_task = None

        # 3. 实例化新任务（基于当前时间戳生成）
        task = ReportTask(task_id=f"report_{int(time.time())}")

        # 4. 更新单任务槽并将其注册到全局任务字典中
        self.current_task = task
        self.tasks_registry[task.task_id] = task
        return task

    def get_generate_task(self, task_id: str) -> Optional[ReportTask]:
        """根据任务 ID 获取注册表中的任务详情。"""

        # 1. 从注册表字典中返回任务对象
        return self.tasks_registry.get(task_id)