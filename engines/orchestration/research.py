import asyncio
from typing import Awaitable, Callable

from loguru import logger

from engines.common.eventing.event import (
    RoleErrorEvent,
    RoleProgressEvent,
    RoleResultEvent,
)
from engines.common.eventing.publishers import (
    pub_role_error,
    pub_role_progress,
    pub_role_result,
)
from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate
from engines.common.runtime.role_log import route_logs_by_role
from engines.contracts.roles import role_report_dir
from engines.insight_agent.agent import invoke_insight_agent
from engines.media_agent.agent import invoke_media_agent

ProgressCallback = Callable[[ProgressUpdate], None]
AgentInvoker = Callable[[str, str, LLMClient, str, ProgressCallback], Awaitable[None]]

_RESEARCH_INVOKER: dict[str, AgentInvoker] = {
    "insight": invoke_insight_agent,
    "media": invoke_media_agent,
}


def run_research(query: str):
    """并发启动 insight 与 media 研究 Agent"""
    for role in _RESEARCH_INVOKER:
        asyncio.create_task(_run_research_role_task(role, query))


async def _run_research_role_task(role: str, query: str):
    """单角色研究 Agent 后台执行任务"""
    with route_logs_by_role(role):
        _publish_role_progress(
            role=role,
            update=ProgressUpdate(status="starting", message="开始执行研究", progress_pct=0),
        )
        try:
            await _execute_research_flow(role, query)
            pub_role_result(RoleResultEvent(role=role))
        except Exception as e:
            logger.error(f"{role} 研究智能体执行期间出现了异常: {str(e)}")
            pub_role_error(RoleErrorEvent(role=role, error=str(e)))


async def _execute_research_flow(role: str, query: str):
    """装配客户端与目录并调用角色 Agent"""
    llm_client = LLMClient.from_role(role)
    output_dir = role_report_dir(role)  # type: ignore
    await _RESEARCH_INVOKER[role](
        query, role, llm_client, output_dir, lambda update: _publish_role_progress(role, update)
    )


def _publish_role_progress(role: str, update: ProgressUpdate):
    """将进度更新发布为角色进度事件"""
    pub_role_progress(
        RoleProgressEvent(
            role=role,
            status=update.status,
            message=update.message,
            progress_pct=update.progress_pct,
        )
    )
