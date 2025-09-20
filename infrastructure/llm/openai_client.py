"""
原生OpenAI HTTP客户端
替代LangChain，直接使用httpx调用OpenAI兼容的API
"""
import json
from typing import Any

import httpx
from pydantic import BaseModel

from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class Message(BaseModel):
    """消息对象"""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class ToolCall(BaseModel):
    """工具调用对象"""
    id: str
    type: str = "function"
    function: dict[str, Any]  # {"name": "tool_name", "arguments": "json_string"}


class ChatResponse(BaseModel):
    """OpenAI聊天响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, Any] | None = None

    @property
    def content(self) -> str:
        """获取回复内容"""
        if self.choices and len(self.choices) > 0:
            message = self.choices[0].get("message", {})
            return message.get("content", "")
        return ""

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        """获取工具调用列表"""
        if self.choices and len(self.choices) > 0:
            message = self.choices[0].get("message", {})
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                # 转换为统一格式
                return [
                    {
                        "id": call.get("id", ""),
                        "name": call.get("function", {}).get("name", ""),
                        "args": json.loads(call.get("function", {}).get("arguments", "{}")) if call.get("function", {}).get("arguments") else {},
                        "type": call.get("type", "function")
                    }
                    for call in tool_calls
                ]
        return []


class OpenAIClient:
    """
    原生OpenAI HTTP客户端
    使用httpx直接调用OpenAI兼容的API，替代LangChain
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        timeout: int = 30
    ):
        """初始化OpenAI客户端"""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        # 构建请求头
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Lumi-Pilot-LLM/1.0"
        }

        logger.info("openai_client", f"初始化OpenAI客户端: {model}")

    def _convert_messages(self, messages: list[Message | dict[str, Any]]) -> list[dict[str, Any]]:
        """将消息转换为OpenAI API格式"""
        converted = []
        for msg in messages:
            if isinstance(msg, Message):
                # Pydantic对象转字典
                msg_dict = {
                    "role": msg.role,
                    "content": msg.content
                }
                if msg.name:
                    msg_dict["name"] = msg.name
                if msg.tool_calls:
                    msg_dict["tool_calls"] = msg.tool_calls
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                converted.append(msg_dict)
            elif isinstance(msg, dict):
                # 字典直接使用
                converted.append(msg)
            else:
                # 其他对象尝试转换
                if hasattr(msg, 'content') and hasattr(msg, 'type'):
                    # LangChain消息对象兼容
                    role_mapping = {
                        "system": "system",
                        "human": "user",
                        "ai": "assistant",
                        "tool": "tool"
                    }
                    converted.append({
                        "role": role_mapping.get(msg.type, "user"),
                        "content": msg.content
                    })
                else:
                    logger.warning("openai_client", f"未知消息格式: {type(msg)}")
                    converted.append({"role": "user", "content": str(msg)})

        return converted

    async def chat_completion(
        self,
        messages: list[Message | dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs
    ) -> ChatResponse:
        """
        发送聊天完成请求

        Args:
            messages: 消息列表
            tools: 工具定义列表
            model: 使用的模型（可覆盖默认值）
            max_tokens: 最大token数（可覆盖默认值）
            temperature: 温度参数（可覆盖默认值）
            **kwargs: 其他参数

        Returns:
            ChatResponse: 聊天响应对象
        """
        # 构建请求数据
        request_data = {
            "model": model or self.model,
            "messages": self._convert_messages(messages),
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            **kwargs
        }

        # 添加工具定义
        if tools:
            request_data["tools"] = tools

        # 发送HTTP请求
        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=url,
                    headers=self.headers,
                    json=request_data
                )

                # 检查HTTP状态码
                if response.status_code != 200:
                    error_text = response.text
                    logger.error("openai_client", f"API请求失败: {response.status_code} - {error_text}")
                    raise Exception(f"Error code: {response.status_code} - {error_text}")

                # 解析响应
                response_data = response.json()
                return ChatResponse(**response_data)

        except httpx.TimeoutException:
            logger.error("openai_client", f"API请求超时: {self.timeout}秒")
            raise Exception(f"API请求超时: {self.timeout}秒")
        except httpx.RequestError as e:
            logger.error("openai_client", f"HTTP请求错误: {str(e)}")
            raise Exception(f"HTTP请求错误: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error("openai_client", f"响应解析错误: {str(e)}")
            raise Exception(f"响应解析错误: {str(e)}")
        except Exception as e:
            logger.error("openai_client", f"未知错误: {str(e)}")
            raise


# 便捷函数，用于创建消息对象
def create_system_message(content: str) -> Message:
    """创建系统消息"""
    return Message(role="system", content=content)


def create_user_message(content: str) -> Message:
    """创建用户消息"""
    return Message(role="user", content=content)


def create_assistant_message(content: str, tool_calls: list[dict[str, Any]] | None = None) -> Message:
    """创建助手消息"""
    return Message(role="assistant", content=content, tool_calls=tool_calls)


def create_tool_message(content: str, tool_call_id: str) -> Message:
    """创建工具响应消息"""
    return Message(role="tool", content=content, tool_call_id=tool_call_id)
