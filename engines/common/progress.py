from dataclasses import dataclass


@dataclass
class ProgressUpdate:
    """
    构建:ProgressUpdate("starting","准备开始分析舆情话题",0)
    """
    status: str  # "plan" "search" "summary"
    message: str  # 节点完成是给的自定义输出文字
    progress_pct: int  # 进度百分比
