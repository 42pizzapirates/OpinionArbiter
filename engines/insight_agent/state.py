"""InsightAgent 私有舆情库研究模块：engines/insight_agent/state.py。"""
from typing import TypedDict
from engines.insight_agent.evidence.models import EvidencePool

class InsightState(TypedDict):
    # 入口参数
    query: str
    role: str
    evidence_pool: EvidencePool




