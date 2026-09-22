from typing import Any

from langgraph.graph import END, START, StateGraph

from engines.host_agent.nodes import build_nodes
from engines.host_agent.state import HostState
from engines.host_agent.judge import Judge


def _route_after_parse(state: HostState) -> str:
    """根据章节解析是否合法路由至累积节点或终止。"""
    return "valid" if state.get("valid") else "invalid"


def _route_after_find(state: HostState) -> str:
    """根据就绪配对是否存在路由至研判或终止。"""
    return "judge" if state.get("ready_pairs") else "done"


def _route_after_record(state: HostState) -> str:
    """全部维度研判完成则路由至最终报告节点,否则终止。"""
    if state.get("all_done"):
        return "final"
    return "done"


def build_graph(judge: Judge) -> Any:
    """注册节点与条件路由,编译可执行研判图。"""
    graph = StateGraph(HostState)  # type: ignore
    for name, node in build_nodes(judge).items():
        graph.add_node(name, node)
    graph.add_edge(START, "parse_section")
    graph.add_conditional_edges(
        "parse_section",
        _route_after_parse,
        {"valid": "accumulate_section", "invalid": END},
    )
    graph.add_edge("accumulate_section", "find_ready_pairs")
    graph.add_conditional_edges(
        "find_ready_pairs", _route_after_find, {"judge": "judge_section", "done": END}
    )
    graph.add_edge("judge_section", "record_judgement")
    graph.add_conditional_edges(
        "record_judgement",
        _route_after_record,
        {"final": "generate_final_report", "done": END},
    )
    graph.add_edge("generate_final_report", "save_report")
    graph.add_edge("save_report", END)
    return graph.compile()
