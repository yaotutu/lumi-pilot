"""
统一数据模型定义
包含所有服务共享的基础数据结构
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    """请求上下文信息"""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    session_id: Optional[str] = None


class ResponseMetadata(BaseModel):
    """响应元数据"""
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    duration: Optional[float] = None
    service_name: str
    action: str
    app_name: str = "Lumi Pilot"
    version: str = "0.2.0"


class ServiceRequest(BaseModel):
    """统一服务请求模型"""
    action: str
    payload: Dict[str, Any]
    context: Optional[RequestContext] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data):
        if 'context' not in data or data['context'] is None:
            data['context'] = RequestContext()
        super().__init__(**data)


class ServiceResponse(BaseModel):
    """统一服务响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: ResponseMetadata
    
    @classmethod
    def success_response(
        cls,
        data: Dict[str, Any],
        service_name: str,
        action: str,
        request_id: str,
        duration: Optional[float] = None
    ) -> 'ServiceResponse':
        """创建成功响应"""
        return cls(
            success=True,
            data=data,
            metadata=ResponseMetadata(
                request_id=request_id,
                duration=duration,
                service_name=service_name,
                action=action
            )
        )
    
    @classmethod
    def error_response(
        cls,
        error: str,
        service_name: str,
        action: str,
        request_id: str,
        duration: Optional[float] = None
    ) -> 'ServiceResponse':
        """创建错误响应"""
        return cls(
            success=False,
            error=error,
            metadata=ResponseMetadata(
                request_id=request_id,
                duration=duration,
                service_name=service_name,
                action=action
            )
        )


class HealthStatus(BaseModel):
    """健康状态模型"""
    healthy: bool
    service_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None