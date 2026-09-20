"""公共基础设施模块：engines/common/io/report_io.py。"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path






def save_md_report(output_dir: str , prefix: str, query: str, content: str, suffix: str = ".md") -> Path:
    """直接完成从命名到落盘的全流程"""
    stem = f"{prefix}_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    path = Path(output_dir) / f"{stem}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
