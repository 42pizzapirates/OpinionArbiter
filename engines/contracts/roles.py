from dataclasses import dataclass
from typing import Literal

from engines.contracts.config import get_settings
from engines.insight_agent.prompts import FORMAT_SYSTEM_PROMPT_TEMPLATE
from engines.media_agent.prompts import SYSTEM_PROMPT_FORMAT

ROLE_KEY = Literal["insight", "media", "report", "host"]


@dataclass
class RoleInfo:
    """角色元信息(配置前缀/展示名/目录/提示词)"""

    config_prefix: str
    display_name: str
    report_dir_setting: str
    format_system_prompt: str = ""


ROLE_INFOS: dict[ROLE_KEY, RoleInfo] = {
    "insight": RoleInfo(
        config_prefix="INSIGHT_ENGINE",
        display_name="私域检索智能体专家",
        format_system_prompt=FORMAT_SYSTEM_PROMPT_TEMPLATE,
        report_dir_setting="INSIGHT_REPORT_DIR",
    ),
    "media": RoleInfo(
        config_prefix="MEDIA_ENGINE",
        display_name="公域检索智能体专家",
        format_system_prompt=SYSTEM_PROMPT_FORMAT,
        report_dir_setting="MEDIA_REPORT_DIR",
    ),
    "report": RoleInfo(
        config_prefix="REPORT_ENGINE",
        display_name="报告引擎智能体专家",
        report_dir_setting="OUTPUT_DIR",
    ),
    "host": RoleInfo(
        config_prefix="HOST",
        display_name="研判智能体专家",
        report_dir_setting="HOST_REPORT_DIR",
    ),
}


def role_display_name(role_key: ROLE_KEY) -> str:
    """返回角色的中文展示名"""
    agent_role_info = ROLE_INFOS.get(role_key)
    return agent_role_info.display_name


def role_report_dir(role_key: ROLE_KEY) -> str:
    """返回指定角色的报告输出目录"""
    return getattr(get_settings(), ROLE_INFOS[role_key].report_dir_setting)


def role_report_dirs(role_keys: tuple[ROLE_KEY, ...]) -> dict[str, str]:
    """返回 {role: report_dir} 映射"""
    return {role_key: role_report_dir(role_key) for role_key in role_keys}


def default_roles() -> tuple[ROLE_KEY, ...]:
    """返回默认研究角色(排除 report)"""
    return tuple(key for key in ROLE_INFOS if key != "report")


def default_report_dirs() -> dict[str, str]:
    """返回默认角色的报告目录映射"""
    return role_report_dirs(default_roles())
