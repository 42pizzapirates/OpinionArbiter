from dataclasses import dataclass, field
from typing import Any, TypedDict

from engines.common.eventing.event import HostDiscussionMessageEvent
from engines.host_agent.pair_store import PairStore
from engines.host_agent.schemas import SectionJudgement, SectionPair, SectionResult


class HostState(TypedDict, total=False):
    """LangGraph 运行时状态契约(节点间流转)。"""

    incoming: dict[str, Any]
    section_result: SectionResult
    valid: bool
    query: str
    pair_store: PairStore
    ready_pairs: list[SectionPair]
    current_pair: SectionPair
    current_judgement: SectionJudgement | None
    judgements: list[SectionJudgement]
    all_done: bool
    final_report: str | None
    outbox: list[HostDiscussionMessageEvent]


@dataclass(slots=True)
class Session:
    """跨事件研判会话,桥接图运行状态。"""

    pair_store: PairStore = field(default_factory=PairStore)
    judgements: list[SectionJudgement] = field(default_factory=list)

    def clear(self) -> None:
        """重置配对存储与已积累的研判列表。"""
        self.pair_store.clear()
        self.judgements.clear()

    def to_state(self, incoming: dict[str, Any]) -> HostState:
        """图执行前注入跨事件会话状态。"""
        return {
            "incoming": incoming,
            "pair_store": self.pair_store,
            "judgements": list(self.judgements),
            "outbox": [],
        }

    def apply_state(self, state: HostState) -> None:
        """图执行后回收研判列表以维持跨事件会话。"""
        self.judgements = list(state.get("judgements"))
