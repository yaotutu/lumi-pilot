"""
故障检测服务专用数据模型
"""
from typing import Any

from pydantic import BaseModel


class LogAnalysisRequest(BaseModel):
    """日志分析请求模型"""
    logs: list[str]
    log_type: str | None = "application"  # application, system, access, error
    time_range: str | None = None
    severity_filter: str | None = None  # error, warning, info, debug


class AnomalyDetectionRequest(BaseModel):
    """异常检测请求模型"""
    metrics: dict[str, Any]
    baseline: dict[str, Any] | None = None
    threshold: float | None = 0.8
    detection_type: str | None = "statistical"  # statistical, ml, rule_based


class SystemDiagnosisRequest(BaseModel):
    """系统诊断请求模型"""
    system_info: dict[str, Any]
    symptoms: list[str]
    context: str | None = None
