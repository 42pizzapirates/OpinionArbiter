from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class DiscussionRecord:
    source: str
    message_text: str
    sent_at: str
    dimension_key: str


class DiscussionBuffer:

    def __init__(self) -> None:
        self._discuss_records: list[DiscussionRecord] = []  # Redis足够(后端用的最多：MySQL)

    def append_message(self, data: dict[str, Any]) -> None:
        self._discuss_records.append(DiscussionRecord(
            source=data.get("source") or "",
            message_text=data.get("content"),
            sent_at=data.get("timestamp") or datetime.now().strftime("%H:%M:%S"),
            dimension_key=data.get("section_key"),
        ))

    def read_messages(self) -> dict[str, Any]:
        return {
            "discussion_records": [
                {
                    "source": record.source,
                    "message_text": record.message_text,
                    "sent_at": record.sent_at,
                    "dimension_key": record.dimension_key
                }
                for record in self._discuss_records
            ]}
