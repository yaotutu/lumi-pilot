"""
3D打印机监控服务专用数据模型
"""
from typing import Any, Optional

from pydantic import BaseModel, Field

from infrastructure.config.settings import get_settings


def get_default_camera_url() -> str:
    """获取默认摄像头URL"""
    try:
        settings = get_settings()
        return settings.printer_monitoring.camera_url
    except Exception:
        return "http://192.168.1.100/webcam/?action=stream"  # 备用默认值


class PrinterStatusRequest(BaseModel):
    """3D打印机状态检测请求模型"""
    camera_url: str = Field(default_factory=get_default_camera_url, description="摄像头URL")
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
