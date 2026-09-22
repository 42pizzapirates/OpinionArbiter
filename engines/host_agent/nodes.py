from typing import Any, Callable

from loguru import logger

from engines.common.io.report_io import save_report
from engines.contracts.config import get_settings
from engines.contracts.dimensions import DIMENSIONS
from engines.host_agent.judge import Judge
from engines.host_agent.mappers import (
    append_event,
    build_agent_event,
    build_final_event,
    build_judgement_event,
)
from engines.host_agent.schemas import SectionResult
from engines.host_agent.state import HostState
from engines.contracts.roles import role_display_name


def parse_section(state: HostState) -> HostState:
    """校验章节就绪事件的来源与维度合法性。"""
    section_result = SectionResult.from_event(state.get("incoming"))
    agent_name = role_display_name("host")
    logger.info(
        f"【{agent_name}】 [section_ready] 事件已收到 章节={section_result.section_key} 源自={section_result.source}"
    )
    valid = section_result.source in {"insight", "media"} and section_result.section_key in DIMENSIONS
    if not valid:
        logger.warning(
            f"【{agent_name}】dropped [section_ready] 事件 章节={section_result.section_key} 源自={section_result.source}"
        )
    return {"section_result": section_result, "valid": valid}


def accumulate_section(state: HostState) -> HostState:
    """章节结果入队,接受时发 Agent 发言消息。"""
    result = state["section_result"]
    pair_store = state["pair_store"]
    if not pair_store.add(result):
        return {"query": result.query}
    return {
        "query": result.query,
        "outbox": append_event(state.get("outbox"), build_agent_event(result)),
    }


def find_ready_pairs(state: HostState) -> HostState:
    """找出 insight+media 都到齐且未研判的维度配对。"""
    return {"ready_pairs": state["pair_store"].ready_pairs()}


def record_judgement(state: HostState) -> HostState:
    """记录研判结果并发主持人章节消息。"""
    pair = state["current_pair"]
    judgement = state.get("current_judgement")
    pair_store = state["pair_store"]
    pair_store.mark_done(pair.section_key)
    updates = {
        "all_done": pair_store.all_done(),
    }
    if judgement:
        updates["judgements"] = [*state.get("judgements"), judgement]
        updates["outbox"] = append_event(state.get("outbox"), build_judgement_event(judgement))
    return updates


def build_judge_section(judge: Judge) -> Callable[[HostState], Any]:
    """返回研判首就绪配对的图节点(含降级)。"""

    async def judge_section(state: HostState) -> HostState:
        """调用 Judge 研判首就绪配对(可降级)。"""
        agent_name = role_display_name("host")
        section_pair = state["ready_pairs"][0]
        logger.info(f"【{agent_name}】 收到两个Agent的同一章节 [{section_pair.section_key}], 开始研判")
        judgement = await judge.judge_section(section_pair, list(state.get("judgements")))
        logger.info(f"【{agent_name}】 章节研判完成, 章节={section_pair.section_key}")
        return {"current_pair": section_pair, "current_judgement": judgement}

    return judge_section


def build_generate_final_report(judge: Judge) -> Callable[[HostState], Any]:
    """LLM 生成最终裁判报告;发 host 最终事件。"""

    async def generate_final_report(state: HostState) -> HostState:
        """调用 Judge 生成最终报告并发布主持人最终事件。"""
        report = await judge.generate_final_report(list(state.get("judgements")))
        if not report:
            return {"final_report": None}
        return {
            "final_report": report,
            "outbox": append_event(state.get("outbox"), build_final_event(report)),
        }

    return generate_final_report


def save_host_report(state: HostState) -> HostState:
    """最终报告 .md 落盘"""
    report = state.get("final_report")
    if not report:
        return {}
    output_dir = get_settings().HOST_REPORT_DIR
    md_path = save_report(output_dir, "host", state["query"], report)
    logger.info(f"HostAgent: 最终报告已落盘 {md_path}")
    return {}


def build_nodes(judge: Judge) -> dict[str, Callable[..., Any]]:
    """返回图节点注册表,直接注入 Judge。"""
    return {
        "parse_section": parse_section,
        "accumulate_section": accumulate_section,
        "find_ready_pairs": find_ready_pairs,
        "judge_section": build_judge_section(judge),
        "record_judgement": record_judgement,
        "generate_final_report": build_generate_final_report(judge),
        "save_report": save_host_report,
    }
