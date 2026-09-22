from dataclasses import dataclass, field
import json

from langchain_core.prompts import PromptTemplate

from engines.common.llm.llm_client import LLMClient
from engines.common.llm.llm_output import sanitize_markdown
from engines.common.runtime.call_retry import with_graceful_retry
from engines.host_agent import prompts
from engines.host_agent.schemas import SectionJudgement, SectionPair, SectionResult


@dataclass(slots=True)
class Judge:
    """主持人研判专家,调用 LLM 输出章节裁决与最终报告。"""

    llm: LLMClient = field(default_factory=lambda: LLMClient.from_role("host"))

    async def judge_section(
            self,
            pair: SectionPair,
            previous: list[SectionJudgement],
    ) -> SectionJudgement | None:
        """调用 LLM 裁决配对章节并清洗 Markdown。"""
        content = await self._call_llm(
            prompts.SYSTEM_PROMPT,
            PromptTemplate.from_template(prompts.SECTION_USER_PROMPT_TEMPLATE).format(
                evidence=self._build_section_evidence(pair, previous)
            ),
        )
        if content is None:
            return None
        return SectionJudgement(section_key=pair.section_key, content=sanitize_markdown(content))

    async def generate_final_report(self, results: list[SectionJudgement]) -> str | None:
        """汇总各维度研判,调用 LLM 生成并清洗最终报告。"""
        content = await self._call_llm(
            prompts.FINAL_SYSTEM_PROMPT,
            PromptTemplate.from_template(prompts.FINAL_USER_PROMPT_TEMPLATE).format(
                evidence=self._build_final_evidence(results)
            ),
        )
        if content is None:
            return None
        return sanitize_markdown(content)

    def _build_section_evidence(self, pair: SectionPair, previous: list[SectionJudgement]) -> str:
        """拼装配对章节证据与近三次历史研判为 LLM 输入。"""
        section_evidence = {
            "section": {"key": pair.section_key, "title": pair.title},
            "insight": self._extract_evidence(pair.insight),
            "media": self._extract_evidence(pair.media),
            "previous_host_judgements": [m.to_dict() for m in previous[-3:]],
        }
        return json.dumps(section_evidence, ensure_ascii=False)

    def _build_final_evidence(self, results: list[SectionJudgement]) -> str:
        """将全部维度研判序列化为最终报告 LLM 输入。"""
        return json.dumps([m.to_dict() for m in results], ensure_ascii=False)

    @staticmethod
    def _extract_evidence(result: SectionResult) -> dict:
        """抽取章节结果标题、正文截断与强度等证据字段。"""
        return {
            "title": result.title,
            "body": result.body[:5000],
            "hit_count": result.hit_count,
            "strength": result.strength,
        }

    @with_graceful_retry
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str | None:
        """带重试地调用 host LLM 生成文本,空内容抛错。"""
        content = await self.llm.generate_text(system_prompt, user_prompt)
        if not content:
            raise ValueError("返回空内容")
        return content
