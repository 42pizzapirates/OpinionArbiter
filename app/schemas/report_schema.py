from pydantic import BaseModel, Field, field_validator


class GenerateReportRequest(BaseModel):
    """报告生成请求体。"""

    query: str = Field("智能舆情分析报告", description="报告主题")

    @field_validator("query")
    @classmethod
    def not_blank(cls, v: str) -> str:
        """校验报告主题非空白。"""
        v = v.strip()
        if not v:
            raise ValueError("报告主题不能为空")
        return v


class ReportStatusResponse(BaseModel):
    """报告生成状态响应体。"""

    prepared: bool = False
    found_files: list[str] = Field(default_factory=list)


class GenerateReportResponse(BaseModel):
    """报告生成任务创建响应体。"""

    task_id: str = ""
