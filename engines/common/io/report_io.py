from datetime import datetime
from pathlib import Path


def save_report(
    output_dir: str | Path, prefix: str, query: str, content: str, suffix: str = ".md"
) -> Path:
    """按规则命名并将报告内容落盘"""
    stem = f"{prefix}_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    path = Path(output_dir) / f"{stem}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def markdown_reports(report_output_dir: str | Path) -> list[Path]:
    """列出目录下报告按修改时间倒序"""
    path = Path(report_output_dir)
    return sorted(path.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True)


def latest_markdown_report(output_dir: str | Path) -> Path | None:
    """返回目录中最新的报告文件"""
    return markdown_reports(output_dir)[0]
