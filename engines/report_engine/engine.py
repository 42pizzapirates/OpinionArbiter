from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from langchain_core.prompts import PromptTemplate
from loguru import logger
from engines.common.io.report_io import save_report
from engines.common.llm.llm_client import LLMClient
from engines.report_engine.prompts import REPORT_SYSTEM_PROMPT, REPORT_USER_PROMPT
from engines.report_engine.renderer import render_html, render_markdown
from engines.contracts.config import get_settings


@dataclass(frozen=True)
class ReportInput:
    """综合报告生成所需的原始数据输入载体"""
    query: str
    host_report: str
    media_report: str
    insight_report: str


@dataclass(frozen=True)
class ReportOutput:
    """报告生成完毕后的最终产物数据载体"""
    html_content: str
    report_id: str
    report_filepath: str
    report_filename: str
    markdown_filepath: str
    markdown_filename: str


class ReportEngine:
    """报告生成引擎：负责驱动 LLM 生成 Markdown 报告、渲染 HTML 并落盘"""

    def __init__(self) -> None:
        """初始化报告引擎并绑定LLM客户端"""

        self._llm_client = LLMClient.from_role("report")

    async def generate_report(
            self,
            report_input: ReportInput,
            report_id: Optional[str] = None,
    ) -> ReportOutput:
        """驱动完整综合报告生成的工作流：生成 Markdown、渲染 HTML 并保存文件"""

        report_id = report_id
        markdown = await self._generate_markdown(report_input)

        html = render_html(render_markdown(markdown), report_input.query)

        return self._save_final_report(report_input.query, report_id, markdown, html)

    async def _generate_markdown(self, report_input: ReportInput) -> str:
        """将输入内容填入提示词模板并请求LLM生成 Markdown 报告"""

        user_prompt = PromptTemplate.from_template(REPORT_USER_PROMPT).format(
            query=report_input.query,
            host_report=report_input.host_report,
            insight_report=report_input.insight_report,
            media_report=report_input.media_report,
        )
        return await self._llm_client.generate_text(
            REPORT_SYSTEM_PROMPT,
            user_prompt,
        )

    def _save_final_report(
            self,
            query: str,
            report_id: str,
            markdown: str,
            html: str,
    ) -> ReportOutput:
        """将生成的 Markdown 和 HTML 综合报告写入本地磁盘"""

        report_dir = get_settings().OUTPUT_DIR
        dirpath = Path(report_dir)
        dirpath.mkdir(parents=True, exist_ok=True)

        markdown_path = save_report(dirpath, "report", query, markdown, ".md")
        html_path = save_report(dirpath, "report", query, html, ".html")

        logger.info(f"报告已落盘: {html_path}")

        return ReportOutput(
            html_content=html,
            report_id=report_id,
            report_filepath=str(html_path),
            report_filename=html_path.name,
            markdown_filepath=str(markdown_path),
            markdown_filename=markdown_path.name,
        )
