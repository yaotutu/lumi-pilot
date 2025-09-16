"""
故障检测服务模块
提供AI故障检测和分析功能
"""
from .service import FaultDetectionService
from .models import LogAnalysisRequest, AnomalyDetectionRequest

__all__ = ["FaultDetectionService", "LogAnalysisRequest", "AnomalyDetectionRequest"]