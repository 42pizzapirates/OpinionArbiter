from typing import Any

from langgraph.graph import END, START, StateGraph

from engines.common.nodes.format_node import FormatReportNode
from engines.common.nodes.save_report_node import SaveReportNode
from engines.media_agent.context import MediaContext
from engines.media_agent.nodes import (
    PlanNode,
    SearchNode,
    SectionSummarizeNode,
)
from engines.media_agent.state import MediaState


def _route_after_summarize(state: MediaState) -> str:
    """依据游标判断继续下一章节或收尾。"""
    cursor = state.get("cursor", 0)
    return "next_section" if cursor < len(state.get("sections", [])) else "all_done"


def build_graph(ctx: MediaContext) -> Any:
    """编排规划、检索、摘要、排版与落盘节点。"""
    graph = StateGraph(MediaState)  # type: ignore
    graph.add_node("plan", PlanNode(ctx))  # type: ignore
    graph.add_node("search", SearchNode(ctx))  # type: ignore
    graph.add_node("summarize", SectionSummarizeNode(ctx))  # type: ignore
    graph.add_node("format_report", FormatReportNode(ctx))  # type: ignore
    graph.add_node("persist_report", SaveReportNode(ctx))  # type: ignore
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "summarize")
    graph.add_conditional_edges(
        "summarize",
        _route_after_summarize,
        {"next_section": "summarize", "all_done": "format_report"},
    )
    graph.add_edge("format_report", "persist_report")
    graph.add_edge("persist_report", END)
    return graph.compile()
