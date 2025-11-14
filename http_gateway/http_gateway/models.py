"""
HTTP API 请求和响应模型

使用 Pydantic 定义类型安全的数据模型。
"""

from typing import Optional
from pydantic import BaseModel, Field


# ==================== Chat API ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1)


class ResponseMetadata(BaseModel):
    """响应元数据"""
    request_id: str = Field(..., description="请求唯一ID")
    model: str = Field(..., description="使用的模型名称")
    duration: float = Field(..., description="处理时长（秒）")
    timestamp: str = Field(..., description="时间戳（ISO格式）")


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="AI回复内容")
    error: Optional[str] = Field(default=None, description="错误信息（仅在失败时）")
    metadata: Optional[ResponseMetadata] = Field(default=None, description="响应元数据")


# ==================== Printer Monitor API ====================

class PrinterMonitorRequest(BaseModel):
    """打印机监控请求"""
    camera_url: Optional[str] = Field(
        default=None,
        description="摄像头URL（可选，不提供则使用配置文件中的默认值）"
    )


class PrinterMonitorResponse(BaseModel):
    """打印机监控响应"""
    success: bool = Field(..., description="监控流程是否成功完成")
    has_issues: bool = Field(..., description="是否检测到打印问题")
    issue: str = Field(default="", description="发现的问题描述")
    suggestion: str = Field(default="", description="处理建议")
    confidence: str = Field(default="", description="分析置信度：高/中/低")
    summary: str = Field(default="", description="AI分析总结")
    timestamp: str = Field(..., description="ISO格式时间戳")
    error: Optional[str] = Field(default=None, description="错误信息（仅在失败时）")


# ==================== Health Check API ====================

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态：healthy / unhealthy")
    http_gateway: str = Field(..., description="HTTP网关状态")
    grpc_backend: str = Field(..., description="gRPC后端状态")
    grpc_target: str = Field(..., description="gRPC目标地址")
    timestamp: str = Field(..., description="检查时间戳")
