from pydantic import BaseModel, Field


class InsightSectionPlan(BaseModel):
    """单章节规划结构：标题、章节键与分析目标。"""

    title: str = Field(..., description="当前固定维度下的章节标题")
    section_key: str = Field(..., description="必须严格原样返回固定维度框架中的 section_key")
    goal_analysis_points: list[str] = Field(
        min_length=1,
        max_length=3,
        description="当前固定维度下要覆盖的分析目标,1 到 3 条",
    )


class InsightResearchPlan(BaseModel):
    """五维章节规划结构，固定五个私域分析章节。"""

    sections: list[InsightSectionPlan] = Field(
        min_length=5,
        max_length=5,
        description="固定 5 个报告章节,必须按 fixed_dimensions 的顺序一一生成",
    )
