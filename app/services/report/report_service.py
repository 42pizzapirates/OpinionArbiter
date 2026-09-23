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

        # 1. 注入任务存储器
        self._task_store = task_store
        # 2. 初始化报告输入加载器
        self._input_loader = ReportInputLoader()
        # 3. 初始化报告生成引擎
        self._report_engine = ReportEngine()

    def get_report_status(self) -> dict[str, Any]:
        """获取最终报告输入数据及已发现的文件"""

        # 1. 检查各个角色[insight/media/host]的输入文件是否已准备就绪
        input_status = self._input_loader.check_report_prepared()

        # 2. 组装并返回信息
        return {
            "prepared": input_status["prepared"],
            "found_files": input_status.get("found_files"),
        }

    def start_generate_report_task(self, query: str) -> ReportTask:
        """创建并异步启动一个报告生成任务"""

        # 1. 在存储器中创建一个处于初始化状态的任务
        task = self._task_store.create_generate_task()

        # 2. 丢到后台事件循环中异步执行生成逻辑
        asyncio.create_task(self._run_report_generation(task, query))

        # 3. 立即返回任务实例供前端轮询
        return task

    def get_generate_report_task(self, task_id: str) -> ReportTask:
        """根据任务 ID 查询报告生成任务详情"""

        # 1. 从任务存储器中返回指定任务
        return self._task_store.get_generate_task(task_id)

    def get_download_file(self, task_id: str, file_type: str) -> dict[str, Any]:
        """获取已生成报告文件的下载路径、文件名和媒体类型"""

        # 1. 获取任务，若不存在则抛出找不到异常
        task = self._task_store.get_generate_task(task_id)
        if not task:
            raise LookupError("报告生成任务不存在")

        # 2. 校验任务是否已成功完成
        if task.status != ReportTaskStatus.COMPLETED:
            raise RuntimeError(f"报告生成任务未完成,当前状态: {task.status.value}")

        # 3. 根据文件类型匹配对应的路径和媒体类型
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

        # 4. 返回文件下载所需的元数据
        return {"file_path": file_path, "file_name": file_name, "media_type": media_type}

    async def _run_report_generation(self, task: ReportTask, query: str) -> None:
        """在后台异步执行报告生成的完整工作流"""
        try:
            # 1. 再次确认输入文件是否全部就绪
            input_status = self._input_loader.check_report_prepared()
            if not input_status.get("prepared"):
                logger.exception(f"报告未就绪")
                return

            # 2. 从磁盘加载各角色[insight/media/host]的输入综合报告内容
            report_input = self._input_loader.load_report_input(
                query=query,
                file_paths=input_status.get("latest_files")
            )

            # 3. 调用综合报告引擎生成最终报告
            report_output = await self._report_engine.generate_report(
                report_input=report_input,
                report_id=task.task_id
            )
            # 4. 将生成的综合报告绑定到任务上(供下载综合报告使用)并标记完成
            task.complete_task(report_output)

        except Exception as e:
            # 5. 捕获异常，记录日志并更新任务状态为失败
            logger.exception(f"报告生成失败: {str(e)}")
            task.status = ReportTaskStatus.ERROR
