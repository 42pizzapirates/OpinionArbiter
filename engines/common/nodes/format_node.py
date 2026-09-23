import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger

from engines.common.llm.llm_output import sanitize_markdown
from engines.common.nodes.base_node import BaseNode
from engines.contracts.roles import ROLE_INFOS, RoleInfo, role_display_name
from engines.insight_agent.state import InsightState


class FormatReportNode(BaseNode):
    """整合章节列表为最终研究报告"""

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """触发最终报告排版与进度上报"""
        agent_name = role_display_name(state["role"]) # type: ignore
        self.context.report_progress("formatting", f"{agent_name} 开始格式化最终报告", 70)
        role = state.get("role")
        agent_info = ROLE_INFOS.get(role)  # type: ignore
        query = state.get("query", "未知主题")
        sections = state.get("sections", [])
        logger.info(
            f"【 {agent_name}】开始执行最终报告排版，关于舆论话题: '{query}'，共 {len(sections)} 个章节等待整合..."
        )
        report_context = json.dumps(
            [{"title": section.get("title"), "body": section.get("body")} for section in sections],
            ensure_ascii=False,
        )
        md_report = await self._generate_final_report(agent_info, report_context, query)
        if not md_report:
            logger.warning(f"[{role}] LLM 排版失败或返回为空，执行程序化兜底拼接。")
            md_report = _fallback_report(agent_name, query, sections)
        logger.info(f"【{agent_name}】报告排版完成 ，最终交付文本共计 {len(md_report)} 字。")
        self.context.report_progress("formatting", f"{agent_name} 格式化最终报告完成", 80)
        return {"final_report": md_report, "report_title": query}

    async def _generate_final_report(
        self, agent_info: RoleInfo, report_context: str, query: str
    ) -> str | None:
        """调用 LLM 排版报告，失败返回 None"""
        system_prompt = PromptTemplate.from_template(agent_info.format_system_prompt).format(
            research_topic=query, report_context=report_context
        )
        try:
            raw_text = await self.context.llm_client.generate_text(
                system_prompt=system_prompt,
                user_prompt="请严格按照上述要求和输入数据，输出最终的 Markdown 报告正文。",
            )
            cleaned_text = sanitize_markdown(raw_text)
            return cleaned_text if cleaned_text else None
        except Exception as exc:
            logger.error(f"LLM 报告生成失败: {exc}")
            return None


def _fallback_report(agent_name: str, query: str, sections: list[dict[str, Any]]) -> str:
    """LLM 失败时的程序化兜底报告拼接"""
    lines = [f"# {agent_name} 分析舆论话题:{query}\n"]
    for idx, section in enumerate(sections, 1):
        lines.append(f"\n## {idx}. {section.get('title')}\n\n{section.get('body')}\n")
    return "".join(lines)
