from typing import Any

from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.contracts.roles import role_display_name
from engines.insight_agent.evidence_processor import EvidencePool
from engines.insight_agent.state import InsightState
from engines.insight_agent.tools.retrival_service import InsightRetrivalService


class RetrievalNode(BaseNode):
    """检索节点：调用私域召回服务获取证据。"""

    def __init__(self, context: ResearchNodeContext) -> None:
        """初始化检索节点上下文。"""
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """执行私域召回并初始化证据池。"""
        agent_name = role_display_name(state["role"])  # type: ignore
        self.context.report_progress("searching", f"{agent_name} 开始执行私域信息搜索", 30)
        user_query = state["query"]
        retrival_service = InsightRetrivalService()
        evidence_records = await retrival_service.retrival_evidence(user_query)
        evidence_pool = EvidencePool(
            query=user_query,
            records=evidence_records,
            clusters=[],
        )
        self.context.report_progress("searching", f"{agent_name} 执行私域信息搜索完成", 40)
        return {"evidence_pool": evidence_pool}
