from typing import Any

from loguru import logger

from engines.common.io.report_io import save_report
from engines.common.nodes.base_node import BaseNode
from engines.contracts.roles import ROLE_INFOS, role_display_name
from engines.insight_agent.state import InsightState


class SaveReportNode(BaseNode):
    """将最终报告 Markdown 落盘的节点"""

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """将最终报告 Markdown 落盘并上报完成"""
        agent_name = role_display_name(state["role"])  # type: ignore
        self.context.report_progress("completed", f"{agent_name} 开始保存最终报告", 90)
        role = state.get("role")
        info = ROLE_INFOS.get(role)  # type: ignore
        agent_name = info.display_name
        title = state.get("report_title")
        logger.info(f"【{agent_name}】开始执行报告落盘，准备保存报告: '{title}'...")
        final_report = state.get("final_report")
        if not final_report:
            logger.error(f"【{agent_name}】状态机中缺失 final_report 数据，跳过落盘流程。")
            return {}
        try:
            md_path = save_report(self.context.output_dir, role, title, final_report)
            logger.info(f"【{agent_name}】报告落盘完成,文件已成功保存至: {md_path}")
            self.context.report_progress("completed", f"{agent_name} 保存最终报告完成", 100)
            return {}
        except Exception as exc:
            logger.error(f"【{agent_name}】 报告落盘失败，出现异常: {exc}")
            raise
