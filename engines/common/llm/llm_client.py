from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from engines.common.runtime.call_retry import with_graceful_retry, with_retry
from engines.contracts import config
from engines.contracts.roles import ROLE_INFOS

T = TypeVar("T", bound=BaseModel)


def _adapt_moonshot(params: dict[str, Any], is_structured: bool) -> dict[str, Any]:
    """适配 Moonshot/Kimi 结构化与温度参数"""
    adapted = params.copy()
    if is_structured:
        adapted["extra_body"] = {"thinking": {"type": "disabled"}}
    else:
        adapted["temperature"] = 1.0
    return adapted


def _prepend_time_context(user_prompt: str) -> str:
    """在用户提示前注入当前时间上下文"""
    current_time = datetime.now().strftime("%Y年%m月%d日%H时%M分")
    time_prefix = f"今天的实际时间是{current_time}"
    if user_prompt:
        return f"{time_prefix}\n{user_prompt}"
    return time_prefix


def _format_messages(system_prompt: str, user_prompt: str) -> list[BaseMessage]:
    """组装系统/用户消息并注入时间"""
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=_prepend_time_context(user_prompt)),
    ]


_PROVIDER_ADAPTERS: dict[str, Callable[[dict[str, Any], bool], dict[str, Any]]] = {
    "moonshot": _adapt_moonshot,
    "kimi": _adapt_moonshot,
}


class LLMClient:
    """LLM 客户端封装：统一调用与重试"""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: Optional[str] = None,
        engine_name: str = "Engine",
        model_provider: str = "openai",
        timeout: float = 1800,
    ) -> None:
        """初始化 LLM 客户端配置"""
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.engine_name = engine_name
        self.model_provider = model_provider
        self.timeout = timeout

    @classmethod
    def from_role(cls, role: str) -> "LLMClient":
        """按角色名从全局配置构造客户端"""
        role_info = ROLE_INFOS.get(role) # type: ignore
        role_info_prefix = role_info.config_prefix
        return cls(
            api_key=getattr(config.get_settings(), f"{role_info_prefix}_API_KEY"),
            model_name=getattr(config.get_settings(), f"{role_info_prefix}_MODEL_NAME"),
            base_url=getattr(config.get_settings(), f"{role_info_prefix}_BASE_URL"),
            engine_name=role_info.display_name,
            model_provider=getattr(config.get_settings(), f"{role_info_prefix}_MODEL_PROVIDER"),
        )

    @with_retry
    async def generate_text(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """流式生成文本(规避网关超时+重试)"""
        llm = self._build_chat_model(is_structured=False, **kwargs)
        text_chunks = []
        async for chunk in llm.astream(_format_messages(system_prompt, user_prompt)):
            text = chunk.text
            if text:
                text_chunks.append(text)
        return "".join(text_chunks)

    @with_retry
    async def generate_object(
        self, system_prompt: str, user_prompt: str, output_model: type[T], **kwargs
    ) -> T:
        """结构化输出：调用 LLM 返回指定模型实例"""
        llm = self._build_chat_model(is_structured=True, **kwargs)
        structured = llm.with_structured_output(output_model, method="function_calling")
        result = await structured.ainvoke(_format_messages(system_prompt, user_prompt))
        if result is None:
            raise ValueError(f"{self.engine_name} 返回 None")
        return result

    def _build_chat_model(self, is_structured: bool, **kwargs):
        """构造 LangChain ChatModel 并应用厂商适配"""
        params = self._adapt_provider_params(kwargs, is_structured)
        return init_chat_model(
            model=self.model_name,
            model_provider=self.model_provider,
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=0,
            **params,
        )

    def _adapt_provider_params(self, kwargs: dict[str, Any], is_structured: bool) -> dict[str, Any]:
        """按模型名匹配厂商参数适配器"""
        model = self.model_name.lower()
        for keyword, adapter in _PROVIDER_ADAPTERS.items():
            if keyword in model:
                return adapter(kwargs, is_structured)
        return kwargs

