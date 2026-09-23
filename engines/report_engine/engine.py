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
    query: str  # 研究主题查询词
    host_report: str  # 主持人裁判报告内容
    media_report: str  # 媒体传播报告内容
    insight_report: str  # 数据挖掘报告内容


@dataclass(frozen=True)
class ReportOutput:
    """报告生成完毕后的最终产物数据载体"""
    html_content: str  # 生成的 HTML 报告文本内容
    report_id: str  # 报告任务唯一标识符
    report_filepath: str  # HTML 报告在磁盘上的绝对路径
    report_filename: str  # HTML 报告的文件名
    markdown_filepath: str  # Markdown 报告在磁盘上的绝对路径
    markdown_filename: str  # Markdown 报告的文件名


class ReportEngine:
    """报告生成引擎：负责驱动 LLM 生成 Markdown 报告、渲染 HTML 并落盘"""

    def __init__(self) -> None:
        """初始化报告引擎并绑定LLM客户端"""

        # 1. 实例化专门用于报告生成角色的 LLM 客户端
        self._llm_client = LLMClient.from_role("report")

    async def generate_report(
            self,
            report_input: ReportInput,
            report_id: Optional[str] = None,
    ) -> ReportOutput:
        """驱动完整综合报告生成的工作流：生成 Markdown、渲染 HTML 并保存文件"""

        report_id = report_id
        # 1. 调用LLM生成 Markdown 格式的综合报告内容
        markdown = await self._generate_markdown(report_input)

        # 2. 将 Markdown 渲染为 HTML 格式文本
        html = render_html(render_markdown(markdown), report_input.query)

        # 3. 将生成的 Markdown 和 HTML 文件保存到本地磁盘并返回元数据
        return self._save_final_report(report_input.query, report_id, markdown, html)

    async def _generate_markdown(self, report_input: ReportInput) -> str:
        """将输入内容填入提示词模板并请求LLM生成 Markdown 报告"""

        # 1. 使用 LangChain 模板注入实际的综合报告材料
        user_prompt = PromptTemplate.from_template(REPORT_USER_PROMPT).format(
            query=report_input.query,
            host_report=report_input.host_report,
            insight_report=report_input.insight_report,
            media_report=report_input.media_report,
        )
        # 2. 调用大模型生成最终的 Markdown 文本
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

        # 1. 从配置中获取报告输出目录并确保目录存在
        report_dir = get_settings().OUTPUT_DIR
        dirpath = Path(report_dir)
        dirpath.mkdir(parents=True, exist_ok=True)

        # 2. 将 Markdown 和 HTML 报告分别保存到磁盘
        markdown_path = save_report(dirpath, "report", query, markdown, ".md")
        html_path = save_report(dirpath, "report", query, html, ".html")

        # 3. 记录落盘成功日志并组装返回综合报告元数据
        logger.info(f"报告已落盘: {html_path}")

        return ReportOutput(
            html_content=html,
            report_id=report_id,
            report_filepath=str(html_path),
            report_filename=html_path.name,
            markdown_filepath=str(markdown_path),
            markdown_filename=markdown_path.name,
        )
