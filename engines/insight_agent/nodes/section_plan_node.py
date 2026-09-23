import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger

from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.contracts.dimensions import DIMENSIONS, get_insight_dimensions
from engines.contracts.roles import role_display_name
from engines.insight_agent.evidence_processor import (
    EvidencePool,
    generate_plan_overview,
)
from engines.insight_agent.prompts import PLAN_SYSTEM_PROMPT, PLAN_USER_PROMPT_TEMPLATE
from engines.insight_agent.schemas import InsightResearchPlan
from engines.insight_agent.state import InsightSection, InsightState


class SectionPlanNode(BaseNode):
    """章节规划节点：LLM 生成五维章节计划。"""

    def __init__(self, context: ResearchNodeContext) -> None:
        """初始化章节规划节点上下文。"""
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """调用 LLM 规划五维章节并回写章节列表。"""
        agent_name = role_display_name(state["role"])  # type: ignore
        logger.info(f"【{agent_name}】 开始进行章节规划，当前研究主题: '{state.get('query')}'")
        self.context.report_progress("planning", f"{agent_name} 开始执行私域五维搜索信息规划", 10)
        plan_user_prompt = self._build_plan_prompt(state)
        plan: InsightResearchPlan = await self.context.llm_client.generate_object(
            PLAN_SYSTEM_PROMPT, plan_user_prompt, InsightResearchPlan
        )
        sections = self.generate_insight_section(plan)
        section_keys = ", ".join(s.get("section_key", "") for s in sections)
        logger.info(f"【{agent_name}】章节规划完成，共规划 {len(sections)} 个章节信息，包含: {section_keys}")
        self.context.report_progress("planning", f"{agent_name} 规划私域五维搜索信息完成", 20)
        return {"sections": sections}

    def _build_plan_prompt(self, state: InsightState) -> str:
        """拼装五维框架与证据总览的规划提示词。"""
        pool: EvidencePool = state["evidence_pool"]
        research_topic = state["query"]
        fixed_dimensions_data = get_insight_dimensions()
        plan_overview_evidence = generate_plan_overview(pool)
        prompt_template = PromptTemplate.from_template(PLAN_USER_PROMPT_TEMPLATE)
        return prompt_template.format(
            research_topic=research_topic,
            fixed_dimensions=json.dumps(fixed_dimensions_data, ensure_ascii=False, indent=2),
            evidence_overview=json.dumps(plan_overview_evidence, ensure_ascii=False, indent=2),
        )

    def generate_insight_section(self, plan: InsightResearchPlan) -> list[InsightSection]:
        """将 LLM 规划对齐固定五维生成章节。"""
        insight_sections: list[InsightSection] = []
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
            else:
                goals = [dimension.insight_goal]
                title = dimension.title
            insight_sections.append(
                InsightSection(title=title, goal=goals, section_key=dimension.key)
            )
        return insight_sections
