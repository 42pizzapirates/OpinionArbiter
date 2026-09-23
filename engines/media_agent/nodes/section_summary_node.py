import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger

from engines.common.llm.llm_output import sanitize_markdown
from engines.common.nodes.base_node import BaseNode
from engines.contracts.roles import role_display_name
from engines.media_agent.evidence_processor import (
    SectionEvidencePack,
    dispatch_section_ready_event,
    generate_section_evidence_pack,
)
from engines.media_agent.prompts import (
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT_TEMPLATE,
)
from engines.media_agent.state import MediaSection, MediaState

FALLBACK_BODY = "【数据缺口】该维度未在可用数据源中检索到相关内容,本章节暂无分析结论。"


class SectionSummarizeNode(BaseNode):
    """基于全局证据撰写章节分析并发布就绪事件。"""

    async def __call__(self, state: MediaState) -> dict[str, Any]:
        agent_name = role_display_name(state["role"])  # type: ignore
        self.context.report_progress("summary", f"{agent_name} 生成章节摘要完成", 50)
        cursor = state.get("cursor", 0)
        sections = list(state.get("sections"))
        if cursor >= len(sections):
            return {"sections": sections}
        section: MediaSection = sections[cursor]
        query = state.get("query")
        records = state.get("search_evidence_records")
        evidence_pack = generate_section_evidence_pack(records=records[:8], used_query=query)
        section["hit_count"] = evidence_pack.evidence_count
        section["evidence_strength"] = evidence_pack.evidence_strength
        if evidence_pack.evidence_count <= 0:
            logger.info(f"【agent_name】 章节 {section.get('section_key')} 证据包为空，跳过生成。")
            section["body"] = FALLBACK_BODY
        else:
            section["body"] = await self._generate_section_body(section, evidence_pack)
        dispatch_section_ready_event(state, cursor, section)
        sections[cursor] = section
        self.context.report_progress("summary", f"{agent_name} 生成章节摘要完成", 60)
        return {"sections": sections, "cursor": cursor + 1}

    async def _generate_section_body(self, section: MediaSection, pack: SectionEvidencePack) -> str:
        """调用 LLM 按证据包生成章节正文。"""
        section_plan = {
            "title": section.get("title"),
            "section_key": section.get("section_key"),
            "expected_analysis_points": section.get("goal"),
        }
        user_prompt = PromptTemplate.from_template(SUMMARY_USER_PROMPT_TEMPLATE).format(
            used_query=pack.used_query,
            section_plan=json.dumps(section_plan, ensure_ascii=False, indent=2),
            evidence_strength=pack.evidence_strength,
            search_evidence_results="\n\n".join(pack.evidence_source_blocks),
        )
        try:
            body = await self.context.llm_client.generate_text(SUMMARY_SYSTEM_PROMPT, user_prompt)
            return sanitize_markdown(body)
        except Exception as exc:
            logger.error(f"LLM章节摘要生成失败: {exc}")
            return FALLBACK_BODY
