from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from loguru import logger

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


@contextmanager
def route_logs_by_role(role: str) -> Iterator[None]:
    """按角色分流日志到独立文件"""
    handler_id = None
    with logger.contextualize(role=role):
        try:
            _LOG_DIR.mkdir(parents=True, exist_ok=True)
            handler_id = logger.add(
                str(_LOG_DIR / f"{role}.log"),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[role]}] {name} - {message}",
                level="INFO",
                encoding="utf-8",
                rotation="1 MB",
                filter=lambda record: record["extra"].get("role") == role,
            )
            yield
        except Exception as exc:
            raise exc
        finally:
            if handler_id is not None:
                logger.remove(handler_id)
