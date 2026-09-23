from typing import Callable

from loguru import logger

from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate
from engines.contracts.roles import role_display_name
from engines.media_agent.context import MediaContext
from engines.media_agent.graph import build_graph


async def invoke_media_agent(
        query: str,
        role: str,
        llm_client: LLMClient,
        output_dir: str,
        progress_callback: Callable[[ProgressUpdate], None] | None = None,
) -> None:
    """构建媒体研究上下文并执行 LangGraph 研究图。"""
    agent_name = role_display_name(role)  # type: ignore
    logger.info(f"【{agent_name}】开始研究: {query}")
    context = MediaContext(
        role=role, llm_client=llm_client, output_dir=output_dir, progress_callback=progress_callback
    )
    graph = build_graph(context)
    initial_state = {"query": query, "role": role}
    await graph.ainvoke(initial_state)
    logger.info(f"【{agent_name}】研究完成")
