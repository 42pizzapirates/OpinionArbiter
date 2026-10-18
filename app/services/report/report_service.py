import asyncio
from typing import Any
from loguru import logger
from app.services.report.input_loader import ReportInputLoader
from app.services.report.task_store import ReportTask, ReportTaskStatus, ReportTaskStore
from engines.report_engine.engine import ReportEngine


class ReportService:
    """综合报告服务：协调输入加载、任务状态跟踪与报告引擎生成报告"""

    def __init__(
            self,
            task_store: ReportTaskStore
    ) -> None:
        """初始化最终综合报告服务以及组件"""

        self._task_store = task_store
        self._input_loader = ReportInputLoader()
        self._report_engine = ReportEngine()

    def get_report_status(self) -> dict[str, Any]:
        """获取最终报告输入数据及已发现的文件"""

        input_status = self._input_loader.check_report_prepared()

        return {
            "prepared": input_status["prepared"],
            "found_files": input_status.get("found_files"),
        }

    def start_generate_report_task(self, query: str) -> ReportTask:
        """创建并异步启动一个报告生成任务"""

        task = self._task_store.create_generate_task()

        asyncio.create_task(self._run_report_generation(task, query))

        return task

    def get_generate_report_task(self, task_id: str) -> ReportTask:
        """根据任务 ID 查询报告生成任务详情"""

        return self._task_store.get_generate_task(task_id)

    def get_download_file(self, task_id: str, file_type: str) -> dict[str, Any]:
        """获取已生成报告文件的下载路径、文件名和媒体类型"""

        task = self._task_store.get_generate_task(task_id)
        if not task:
            raise LookupError("报告生成任务不存在")

        if task.status != ReportTaskStatus.COMPLETED:
            raise RuntimeError(f"报告生成任务未完成,当前状态: {task.status.value}")

        if file_type == "html":
            file_path = task.report_file_path
            file_name = task.report_file_name
            media_type = "text/html"
        elif file_type == "md":
            file_path = task.markdown_file_path
            file_name = task.markdown_file_name
            media_type = "text/markdown"
        else:
            raise ValueError("不支持的报告文件类型")

        return {"file_path": file_path, "file_name": file_name, "media_type": media_type}

    async def _run_report_generation(self, task: ReportTask, query: str) -> None:
        """在后台异步执行报告生成的完整工作流"""
        try:
            input_status = self._input_loader.check_report_prepared()
            if not input_status.get("prepared"):
                logger.exception(f"报告未就绪")
                return

            report_input = self._input_loader.load_report_input(
                query=query,
                file_paths=input_status.get("latest_files")
            )

            report_output = await self._report_engine.generate_report(
                report_input=report_input,
                report_id=task.task_id
            )
            task.complete_task(report_output)

        except Exception as e:
            logger.exception(f"报告生成失败: {str(e)}")
            task.status = ReportTaskStatus.ERROR
