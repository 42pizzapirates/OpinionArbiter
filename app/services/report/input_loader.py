from typing import Any
from pathlib import Path
from engines.common.io.report_io import markdown_reports
from engines.contracts.roles import default_report_dirs, default_roles
from engines.report_engine.engine import ReportInput


class ReportInputLoader:
    """报告输入加载器：负责检查和读取各角色[insight/media/host]生成的报告源文件。"""

    def check_report_prepared(self) -> dict[str, Any]:
        """检查所有必需角色的报告文件是否已就绪。"""

        # 1. 初始化收集器，用于存储已发现文件、缺失信息和最新文件
        found_files, missing_files, latest_files = [], [], {}

        # 2. 遍历默认的角色报告目录，检查是否存在 Markdown 报告
        for role_key, dirpath in default_report_dirs().items():
            md_files = markdown_reports(dirpath)
            if md_files:
                found_files.append(f"{role_key}: {len(md_files)} 个文件")
                latest_files[role_key] = str(md_files[0])
            else:
                missing_files.append(f"{role_key}: 目录中没有 .md 文件")

        # 3. 校验是否凑齐 3 个角色的报告，并组装返回状态
        return {
            "prepared": len(latest_files) == 3,
            "found_files": found_files,
            "latest_files": latest_files,
            "missing_files": missing_files
        }

    def load_report_input(self, query: str, file_paths: dict[str, str]) -> ReportInput:
        """读取各角色的 Markdown 报告内容并封装为统一输入对象。"""

        # 1. 遍历默认输入角色，读取对应路径下的文件文本内容
        reports_content: dict[str, str] = {}
        for role_key in default_roles():
            path = file_paths.get(role_key)
            reports_content[f"{role_key}_report"] = Path(path).read_text(encoding="utf-8")

        # 2. 将读取到的内容组装为 ReportInput 实体并返回
        return ReportInput(
            query=query,
            host_report=reports_content["host_report"],
            media_report=reports_content["media_report"],
            insight_report=reports_content["insight_report"]
        )