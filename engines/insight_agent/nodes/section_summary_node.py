import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger

from engines.common.llm.llm_output import sanitize_markdown
from engines.common.nodes.base_node import BaseNode
from engines.contracts.roles import role_display_name
from engines.insight_agent.evidence_processor import (
    SectionEvidencePack,
    dispatch_section_ready_event,
    generate_section_evidence_pack,
)
from engines.insight_agent.prompts import (
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT_TEMPLATE,
)
from engines.insight_agent.state import InsightSection, InsightState

FALLBACK_BODY = "该维度未有相关内容，本章节暂不做延展"


class SectionSummarizeNode(BaseNode):
    """章节摘要节点：基于证据包生成各章节正文。"""

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """按游标取证据包生成章节正文并发布事件。"""
        agent_name = role_display_name(state["role"])  # type: ignore
        self.context.report_progress("summary", f"{agent_name} 开始生成章节摘要", 50)
        section_index = state.get("cursor", 0)
        sections = list(state.get("sections"))
        section_evidence_records = list(state.get("section_evidence_records"))
        if section_index >= len(sections):
            return {"sections": sections}
        section: InsightSection = sections[section_index]
        records = (
            section_evidence_records[section_index]
            if section_index < len(section_evidence_records)
            else []
        )
        pack = generate_section_evidence_pack(state["query"], records)
        section["hit_count"] = pack.evidence_count
        section["evidence_strength"] = pack.strength
        if pack.evidence_count <= 0:
            logger.info(f"章节 {section.get('title')} 证据包为空，跳过生成。")
            section["body"] = FALLBACK_BODY
        else:
            section["body"] = await self._generate_section_body(section, pack)
        dispatch_section_ready_event(state, section_index, section)
        sections[section_index] = section
        self.context.report_progress("summary", f"{agent_name} 生成章节摘要完成", 60)
        return {"sections": sections, "cursor": section_index + 1}

    async def _generate_section_body(
            self, section: InsightSection, pack: SectionEvidencePack
    ) -> str:
        """调用 LLM 生成章节正文并清洗 Markdown。"""
        section_plan = {
            "title": section.get("title"),
            "section_key": section.get("section_key"),
            "expected_analysis_points": section.get("goal"),
        }
        prompt = PromptTemplate.from_template(SUMMARY_USER_PROMPT_TEMPLATE).format(
            used_query=pack.used_query,
            section_plan=json.dumps(section_plan, ensure_ascii=False, indent=2),
            search_evidence_results="\n\n".join(pack.evidence_source_blocks),
            evidence_strength=pack.strength,
        )
        try:
            body = await self.context.llm_client.generate_text(SUMMARY_SYSTEM_PROMPT, prompt)
            return sanitize_markdown(body)
        except Exception as exc:
            logger.error(f"LLM章节摘要生成失败，异常: {exc}")
            return FALLBACK_BODY
