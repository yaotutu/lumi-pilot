"""
聊天服务专用数据模型
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    temperature: float | None = None
    max_tokens: int | None = None


class ChatStreamRequest(BaseModel):
    """流式聊天请求模型"""
    message: str
    temperature: float | None = None
    max_tokens: int | None = None
