"""
聊天服务专用数据模型
"""
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    system_prompt: Optional[str] = None
    character: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatStreamRequest(BaseModel):
    """流式聊天请求模型"""
    message: str
    system_prompt: Optional[str] = None
    character: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None