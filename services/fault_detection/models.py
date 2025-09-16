"""
故障检测服务专用数据模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class LogAnalysisRequest(BaseModel):
    """日志分析请求模型"""
    logs: List[str]
    log_type: Optional[str] = "application"  # application, system, access, error
    time_range: Optional[str] = None
    severity_filter: Optional[str] = None  # error, warning, info, debug


class AnomalyDetectionRequest(BaseModel):
    """异常检测请求模型"""
    metrics: Dict[str, Any]
    baseline: Optional[Dict[str, Any]] = None
    threshold: Optional[float] = 0.8
    detection_type: Optional[str] = "statistical"  # statistical, ml, rule_based


class SystemDiagnosisRequest(BaseModel):
    """系统诊断请求模型"""
    system_info: Dict[str, Any]
    symptoms: List[str]
    context: Optional[str] = None