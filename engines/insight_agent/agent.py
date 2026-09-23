from typing import Callable

from loguru import logger

from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate
from engines.contracts.roles import role_display_name
from engines.insight_agent.context import InsightContext
from engines.insight_agent.graph import build_graph


async def invoke_insight_agent(
        query: str,
        role: str,
        llm_client: LLMClient,
        out_put_dir: str,
        progress_callback: Callable[[ProgressUpdate], None] | None,
):
    """构建私域舆情智能体上下文与图，执行研究流程。"""
    agent_name = role_display_name(role)  # type: ignore
    logger.info(f"【{agent_name}】 开始研究: {query}")
    context = InsightContext(
        role=role,
        llm_client=llm_client,
        output_dir=out_put_dir,
        progress_callback=progress_callback,
    )
    graph = build_graph(context)
    initial_state = {"query": query, "role": role}
    await graph.ainvoke(initial_state)
    logger.info(f"【{agent_name}】 研究完成")
