"""
故障检测服务实现
提供AI驱动的故障检测和系统诊断功能
"""
from typing import Any

from core.models import HealthStatus, ServiceRequest, ServiceResponse
from infrastructure.llm.client import LLMClient

from .models import AnomalyDetectionRequest, LogAnalysisRequest, SystemDiagnosisRequest


class FaultDetectionService:
    """
    故障检测服务类
    提供基于AI的故障检测、日志分析和系统诊断功能
    """

    def __init__(self, llm_client: LLMClient):
        """
        初始化故障检测服务

        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
        self.service_name = "fault_detection"

        # 故障检测专用系统提示词
        self.system_prompts = {
            "log_analysis": """你是一个专业的系统运维和故障分析专家。请分析提供的日志内容，识别潜在的问题、错误模式和异常情况。
请提供：
1. 发现的主要问题和异常
2. 问题的严重程度评估
3. 可能的根本原因分析
4. 建议的解决方案
请以结构化的方式回复，使用中文。""",

            "anomaly_detection": """你是一个数据分析和异常检测专家。请分析提供的系统指标数据，识别异常模式和趋势。
请提供：
1. 检测到的异常指标
2. 异常的类型和特征
3. 异常的可能影响
4. 监控和预防建议
请以结构化的方式回复，使用中文。""",

            "system_diagnosis": """你是一个系统诊断专家。基于提供的系统信息和症状描述，进行全面的系统健康诊断。
请提供：
1. 系统状态评估
2. 发现的问题和风险点
3. 性能瓶颈分析
4. 优化和维护建议
请以结构化的方式回复，使用中文。"""
        }

    async def process(self, request: ServiceRequest) -> ServiceResponse:
        """
        处理故障检测请求

        Args:
            request: 标准化服务请求

        Returns:
            ServiceResponse: 标准化服务响应
        """
        action = request.action
        request_id = request.context.request_id if request.context else "unknown"

        try:
            if action == "analyze_logs":
                return await self._analyze_logs(request, request_id)
            elif action == "detect_anomaly":
                return await self._detect_anomaly(request, request_id)
            elif action == "diagnose_system":
                return await self._diagnose_system(request, request_id)
            else:
                return ServiceResponse.error_response(
                    error=f"不支持的操作: {action}",
                    service_name=self.service_name,
                    action=action,
                    request_id=request_id
                )
        except Exception as e:
            return ServiceResponse.error_response(
                error=f"故障检测处理失败: {str(e)}",
                service_name=self.service_name,
                action=action,
                request_id=request_id
            )

    async def _analyze_logs(self, request: ServiceRequest, request_id: str) -> ServiceResponse:
        """
        分析日志内容

        Args:
            request: 服务请求
            request_id: 请求ID

        Returns:
            ServiceResponse: 服务响应
        """
        log_req = LogAnalysisRequest(**request.payload)

        if not log_req.logs:
            return ServiceResponse.error_response(
                error="日志内容不能为空",
                service_name=self.service_name,
                action="analyze_logs",
                request_id=request_id
            )

        # 构建分析消息
        logs_text = "\n".join(log_req.logs[:100])  # 限制日志数量避免token超限
        message = f"""请分析以下{log_req.log_type}日志：

日志类型: {log_req.log_type}
时间范围: {log_req.time_range or '未指定'}
严重程度过滤: {log_req.severity_filter or '无过滤'}

日志内容:
{logs_text}
"""

        # 调用LLM进行分析
        response = await self.llm_client.chat(
            message=message,
            system_prompt=self.system_prompts["log_analysis"]
        )

        if response.success:
            return ServiceResponse.success_response(
                data={
                    "analysis_result": response.message,
                    "log_count": len(log_req.logs),
                    "log_type": log_req.log_type,
                    "model": response.data.get("model"),
                    "processing_time": response.data.get("duration")
                },
                service_name=self.service_name,
                action="analyze_logs",
                request_id=request_id
            )
        else:
            return ServiceResponse.error_response(
                error=f"日志分析失败: {response.error}",
                service_name=self.service_name,
                action="analyze_logs",
                request_id=request_id
            )

    async def _detect_anomaly(self, request: ServiceRequest, request_id: str) -> ServiceResponse:
        """
        检测异常指标

        Args:
            request: 服务请求
            request_id: 请求ID

        Returns:
            ServiceResponse: 服务响应
        """
        anomaly_req = AnomalyDetectionRequest(**request.payload)

        if not anomaly_req.metrics:
            return ServiceResponse.error_response(
                error="指标数据不能为空",
                service_name=self.service_name,
                action="detect_anomaly",
                request_id=request_id
            )

        # 构建分析消息
        message = f"""请分析以下系统指标数据中的异常：

检测类型: {anomaly_req.detection_type}
异常阈值: {anomaly_req.threshold}

当前指标:
{self._format_metrics(anomaly_req.metrics)}

{f"基线指标: {self._format_metrics(anomaly_req.baseline)}" if anomaly_req.baseline else ""}
"""

        # 调用LLM进行异常检测
        response = await self.llm_client.chat(
            message=message,
            system_prompt=self.system_prompts["anomaly_detection"]
        )

        if response.success:
            return ServiceResponse.success_response(
                data={
                    "anomaly_analysis": response.message,
                    "metrics_count": len(anomaly_req.metrics),
                    "detection_type": anomaly_req.detection_type,
                    "threshold": anomaly_req.threshold,
                    "model": response.data.get("model")
                },
                service_name=self.service_name,
                action="detect_anomaly",
                request_id=request_id
            )
        else:
            return ServiceResponse.error_response(
                error=f"异常检测失败: {response.error}",
                service_name=self.service_name,
                action="detect_anomaly",
                request_id=request_id
            )

    async def _diagnose_system(self, request: ServiceRequest, request_id: str) -> ServiceResponse:
        """
        系统诊断

        Args:
            request: 服务请求
            request_id: 请求ID

        Returns:
            ServiceResponse: 服务响应
        """
        diagnosis_req = SystemDiagnosisRequest(**request.payload)

        if not diagnosis_req.system_info or not diagnosis_req.symptoms:
            return ServiceResponse.error_response(
                error="系统信息和症状描述不能为空",
                service_name=self.service_name,
                action="diagnose_system",
                request_id=request_id
            )

        # 构建诊断消息
        message = f"""请对以下系统进行诊断：

系统信息:
{self._format_metrics(diagnosis_req.system_info)}

观察到的症状:
{chr(10).join(f"- {symptom}" for symptom in diagnosis_req.symptoms)}

{f"额外上下文: {diagnosis_req.context}" if diagnosis_req.context else ""}
"""

        # 调用LLM进行系统诊断
        response = await self.llm_client.chat(
            message=message,
            system_prompt=self.system_prompts["system_diagnosis"]
        )

        if response.success:
            return ServiceResponse.success_response(
                data={
                    "diagnosis_result": response.message,
                    "symptoms_count": len(diagnosis_req.symptoms),
                    "system_metrics": list(diagnosis_req.system_info.keys()),
                    "model": response.data.get("model")
                },
                service_name=self.service_name,
                action="diagnose_system",
                request_id=request_id
            )
        else:
            return ServiceResponse.error_response(
                error=f"系统诊断失败: {response.error}",
                service_name=self.service_name,
                action="diagnose_system",
                request_id=request_id
            )

    def _format_metrics(self, metrics: dict[str, Any]) -> str:
        """
        格式化指标数据为可读文本

        Args:
            metrics: 指标字典

        Returns:
            str: 格式化后的文本
        """
        if not metrics:
            return "无指标数据"

        formatted_lines = []
        for key, value in metrics.items():
            if isinstance(value, (list, dict)):
                formatted_lines.append(f"{key}: {str(value)[:200]}...")
            else:
                formatted_lines.append(f"{key}: {value}")

        return "\n".join(formatted_lines)

    async def health_check(self) -> HealthStatus:
        """
        检查故障检测服务健康状态

        Returns:
            HealthStatus: 健康状态信息
        """
        try:
            # 检查LLM连接
            llm_healthy = await self.llm_client.validate_connection()

            return HealthStatus(
                healthy=llm_healthy,
                service_name=self.service_name,
                details={
                    "llm_connected": llm_healthy,
                    "supported_actions": self.get_supported_actions(),
                    "system_prompts_loaded": len(self.system_prompts)
                }
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                service_name=self.service_name,
                error=f"健康检查失败: {str(e)}"
            )

    def get_service_name(self) -> str:
        """获取服务名称"""
        return self.service_name

    def get_supported_actions(self) -> list[str]:
        """获取支持的操作列表"""
        return ["analyze_logs", "detect_anomaly", "diagnose_system"]
