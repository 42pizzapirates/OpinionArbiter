from typing import Annotated

from fastapi import Depends
from app.services.config_service import ConfigService
from app.services.research_service import ResearchService
from app.services.host_service import HostService
from app.services.report.report_service import ReportService
from app.services.report.task_store import ReportTaskStore


def get_config_service():
    return ConfigService()


ConfigServiceDep = Annotated[ConfigService, Depends(get_config_service)]


def get_research_service():
    return ResearchService()


ResearchServiceDep = Annotated[ResearchService, Depends(get_research_service)]


def get_host_service():
    """
    获取主持人服务
    :return:
    """
    return HostService()


HostServiceDep = Annotated[HostService, Depends(get_host_service)]

_report_service = ReportService(task_store=ReportTaskStore())

def get_report_service():
    """
    获取报告服务(共享)
    :return:
    """
    return _report_service


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
