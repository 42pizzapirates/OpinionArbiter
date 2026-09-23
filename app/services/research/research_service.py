from typing import Any
from engines.orchestration.research import run_research
from engines.contracts.roles import role_report_dirs
from engines.common.io.report_io import latest_markdown_report


class ResearchService:

    def start_research(self, query: str) -> dict[str, Any]:
        # 1. 引擎编排层启动两个研究Agent执行的任务
        try:
            run_research(query)
            return {"started": True}
        except Exception as e:
            return {"started": False, "error": str(e)}

    def get_research_result(self) -> dict[str, Any]:

        research_results: dict[str, Any] = {}
        role_output_dirs = role_report_dirs(role_keys=("insight", "media"))

        for role, output_dir in role_output_dirs.items():
            latest_md = latest_markdown_report(output_dir)
            if not latest_md:
                continue
            research_results[role] = {
                "final_report": latest_md.read_text(encoding="utf-8", errors="ignore"),
                "report_file": str(latest_md),
            }
        return {"results": research_results}
