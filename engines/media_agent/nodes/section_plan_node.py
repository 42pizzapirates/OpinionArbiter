"""MediaAgent 研究蓝图节点：基于研究主题与可用搜索工具，规划媒体侧五维搜索策略。"""

import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger

from engines.common.nodes.base_node import BaseNode
from engines.contracts.dimensions import DIMENSIONS, get_media_dimensions
from engines.contracts.roles import role_display_name
from engines.media_agent.prompts import PLAN_SYSTEM_PROMPT, PLAN_USER_PROMPT_TEMPLATE
from engines.media_agent.schemas import MediaResearchPlan
from engines.media_agent.state import MediaSection, MediaState
from engines.media_agent.web_search.schemas import SearchTool

SEARCH_TOOL_DESCRIPTIONS: dict[SearchTool, str] = {
    "comprehensive_search": "综合搜索,适合全面理解事件、原因、影响和多来源报道。",
    "source_search": "溯源检索,适合获取可核查的网页出处、原始媒体标题和广泛的表面事实。",
    "realtime_search": "实时追踪,适合获取事件的最新进展、舆情热度变化和最新的传播动态。",
}


class PlanNode(BaseNode):
    """将研究主题转为媒体侧五维检索计划。"""

    async def __call__(self, state: MediaState) -> dict[str, Any]:
        """执行五维章节规划的 LLM 调用与组装。"""

        query = state["query"]
        agent_name = role_display_name(state['role'])  # type: ignore
        self.context.report_progress("planning", f"{agent_name} 开始规划公域五维搜索信息", 10)
        logger.info(f"【{agent_name}】 开始进行章节规划，当前研究主题: '{query}'")
        user_prompt = self._build_plan_prompt(query)
        plan: MediaResearchPlan = await self.context.llm_client.generate_object(
            PLAN_SYSTEM_PROMPT, user_prompt, MediaResearchPlan
        )
        sections = self._generate_media_section(plan)
        section_keys = ", ".join(s.get("section_key", "") for s in sections)
        logger.info(f"{agent_name} 章节规划完成，共规划 {len(sections)} 个章节信息，包含: {section_keys}")
        self.context.report_progress("planning", f"{agent_name} 规划公域五维搜索信息完成", 20)
        return {"sections": sections}

    def _build_plan_prompt(self, query: str) -> str:
        """拼装固定维度与可用工具的规划提示词。"""
        fixed_dimensions = get_media_dimensions()
        available_tools = [
            {"name": tool, "description": description}
            for tool, description in SEARCH_TOOL_DESCRIPTIONS.items()
        ]
        return PromptTemplate.from_template(PLAN_USER_PROMPT_TEMPLATE).format(
            research_topic=query,
            fixed_dimensions=json.dumps(fixed_dimensions, ensure_ascii=False, indent=2),
            available_tools=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )

    def _generate_media_section(self, plan: MediaResearchPlan) -> list[MediaSection]:
        """对齐五维框架并补齐缺失章节的检索词。"""
        media_sections: list[MediaSection] = []
        for dimension in DIMENSIONS.values():
            llm_section = next(
                (
                    section
                    for section in plan.sections
                    if section.section_key and section.section_key.strip() == dimension.key
                ),
                None,
            )
            if llm_section:
                goals = [g.strip() for g in llm_section.goal_analysis_points if g.strip()]
                title = llm_section.title.strip()
                search_tool = llm_section.search_tool
                search_keywords = [k.strip() for k in llm_section.search_keywords if k.strip()]
            else:
                goals = [dimension.media_goal]
                title = dimension.title
                search_tool = "comprehensive_search"
                search_keywords = [dimension.title]
            media_sections.append(
                MediaSection(
                    title=title,
                    goal=goals,
                    search_tool=search_tool,  # type: ignore
                    search_keywords=search_keywords,
                    section_key=dimension.key,
                )
            )
        return media_sections
