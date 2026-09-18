from typing import Any
from langgraph.graph import END, START, StateGraph
from engines.insight_agent.context import InsightContext
from engines.insight_agent.nodes.retrieval_node import RetrievalNode
from engines.insight_agent.nodes.rerank_node import RerankNode
from engines.insight_agent.state import InsightState


def build_graph(ctx: InsightContext) -> Any:
    graph = StateGraph(InsightState)

    graph.add_node("retrieval", RetrievalNode(ctx))
    graph.add_node("rank", RerankNode(ctx))
    # graph.add_node("cluster", ClusterNode(ctx))  # type:ignore
    # graph.add_node("plan", PlanNode(ctx))  # type:ignore
    # graph.add_node("section_assign", SectionAssignNode(ctx))  # type:ignore
    # graph.add_node("summarize", SummarizeNode(ctx))  # type:ignore
    # graph.add_node("format_report", FormatReportNode(ctx))  # type:ignore
    # graph.add_node("persist_report", SaveReportNode(ctx))  # type:ignore

    graph.add_edge(START, "retrieval")
    graph.add_edge("retrieval", "rank")
    graph.add_edge("rank", END)
    # graph.add_edge("cluster", "plan")
    # graph.add_edge("plan", "section_assign")
    # graph.add_edge("section_assign", "summarize")
    # graph.add_edge("format_report", "persist_report")
    # graph.add_edge("persist_report", END)

    return graph.compile()
