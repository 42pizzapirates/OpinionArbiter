import asyncio
from typing import Any
from app.services.report.task_store import ReportTaskStore, ReportTask


class ReportService:

    def __init__(
            self,
            task_store: ReportTaskStore
    ) -> None:
        self.task_store = task_store

    def get_report_status(self) -> dict[str, Any]:
        return {
            "inputs_ready": False,
            "files_found": []
        }

    def start_generate_report_task(self, query: str) -> ReportTask:
        task = self.task_store.create_generate_task()
        asyncio.create_task(self._run_report_generation(task, query))
        return task

    def get_generate_report_task(self, task_id: str) -> ReportTask:
        return self.task_store.get_generate_task(task_id)

    def get_download_file(self, task_id: str, file_type: str) -> dict[str, Any]:
        pass

    async def _run_report_generation(self, task: ReportTask, query: str) -> None:
        pass
