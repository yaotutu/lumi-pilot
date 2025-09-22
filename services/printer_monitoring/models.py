"""
3D打印机监控服务专用数据模型
"""
from typing import Any, Optional

from pydantic import BaseModel


class PrinterStatusRequest(BaseModel):
    """3D打印机状态检测请求模型"""
    camera_url: str = "http://192.168.5.18/webcam/?action=stream"  # 默认摄像头URL
    analysis_type: str = "full"  # full, quick, quality_only
    custom_prompt: Optional[str] = None  # 自定义分析提示词


class PrinterStatusResponse(BaseModel):
    """3D打印机状态检测响应模型"""
    success: bool
    status: str  # working, idle, error
    quality_score: int = 0  # 0-100
    issues: list[str] = []
    recommendations: list[str] = []
    safety_alerts: list[str] = []
    summary: str = ""
    image_captured: bool = False
    analysis_model: str = ""
    metadata: dict[str, Any] = {}
    error: Optional[str] = None
