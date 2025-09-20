"""
故障检测服务模块
提供AI故障检测和分析功能
"""
from .models import AnomalyDetectionRequest, LogAnalysisRequest
from .service import FaultDetectionService

__all__ = ["FaultDetectionService", "LogAnalysisRequest", "AnomalyDetectionRequest"]
