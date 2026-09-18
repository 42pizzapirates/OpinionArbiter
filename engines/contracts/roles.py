from typing import Literal
from dataclasses import dataclass

ROLE_KEY: Literal["insight", "media", "report", "host"]


@dataclass
class RoleInfo:
    config_prefix: str
    display_name: str


ROLE_INFOS: dict[str, RoleInfo] = {

    "insight": RoleInfo(
        config_prefix="INSIGHT_ENGINE",
        display_name="私域检索智能体专家"
    ),
    "media": RoleInfo(
        config_prefix="MEDIA_ENGINE",
        display_name="公域检索智能体专家"
    ),
    "report": RoleInfo(
        config_prefix="REPORT_ENGINE",
        display_name="报告引擎智能体专家"
    ),
    "host": RoleInfo(
        config_prefix="HOST",
        display_name="研判智能体专家"
    )

}
