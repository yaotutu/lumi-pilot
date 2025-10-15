"""
gRPC服务处理器
实现简化的Lumi Pilot gRPC接口
"""
import asyncio

import grpc

from core.application import Application
from core.models import ServiceRequest
from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc
from infrastructure.logging import get_logger

# 初始化模块logger
logger = get_logger(__name__)


class LumiPilotServiceHandler(lumi_pilot_pb2_grpc.LumiPilotServiceServicer):
    """
    Lumi Pilot gRPC服务处理器
    提供简洁的AI对话接口
    """

    def __init__(self, application: Application):
        """
        初始化gRPC服务处理器

        Args:
            application: 应用实例，包含所有注册的服务
        """
        self.application = application
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def Chat(self, request: lumi_pilot_pb2.ChatRequest, context: grpc.ServicerContext) -> lumi_pilot_pb2.ChatResponse:
        """
        处理AI对话请求

        Args:
            request: 对话请求
            context: gRPC服务上下文

        Returns:
            lumi_pilot_pb2.ChatResponse: 对话响应
        """
        logger.info("grpc_chat", f"收到对话请求: {request.message}")

        try:
            # 构建服务请求
            service_request = ServiceRequest(
                action="chat",
                payload={
                    "message": request.message,
                }
            )

            # 调用服务
            response = self.loop.run_until_complete(
                self.application.execute("chat", service_request)
            )

            # 构建响应
            if response.success:
                ai_message = response.data.get("message", "")
                logger.info("grpc_chat", f"返回AI回复: {ai_message}")
                return lumi_pilot_pb2.ChatResponse(
                    success=True,
                    message=ai_message,
                    error="",
                    metadata=lumi_pilot_pb2.ResponseMetadata(
                        request_id=response.metadata.request_id,
                        model=response.data.get("model", ""),
                        duration=response.metadata.duration or 0.0,
                        timestamp=response.metadata.timestamp.isoformat()
                    )
                )
            else:
                return lumi_pilot_pb2.ChatResponse(
                    success=False,
                    message="",
                    error=response.error or "未知错误",
                    metadata=lumi_pilot_pb2.ResponseMetadata(
                        request_id=response.metadata.request_id,
                        duration=response.metadata.duration or 0.0,
                        timestamp=response.metadata.timestamp.isoformat()
                    )
                )

        except Exception as e:
            logger.error("grpc_chat", f"对话请求处理失败: {str(e)}")
            return lumi_pilot_pb2.ChatResponse(
                success=False,
                message="",
                error=f"服务内部错误: {str(e)}",
                metadata=lumi_pilot_pb2.ResponseMetadata(
                    request_id="error",
                    timestamp=str(__import__('time').time())
                )
            )

    def MonitorPrinter(self, request: lumi_pilot_pb2.PrinterMonitorRequest, context: grpc.ServicerContext) -> lumi_pilot_pb2.PrinterMonitorResponse:
        """
        处理3D打印机监控请求：截图 + AI分析的完整流程

        Args:
            request: 打印机监控请求
            context: gRPC服务上下文

        Returns:
            lumi_pilot_pb2.PrinterMonitorResponse: 监控响应
        """
        camera_url = request.camera_url or ""  # 可选参数
        logger.info("grpc_printer", f"收到打印机监控请求, 摄像头URL: {camera_url if camera_url else '使用默认'}")

        try:
            # 构建服务请求
            payload = {}
            if camera_url:
                payload["camera_url"] = camera_url

            service_request = ServiceRequest(
                action="check_printer_status",
                payload=payload
            )

            # 调用打印机监控服务
            response = self.loop.run_until_complete(
                self.application.execute("printer_monitoring", service_request)
            )

            # 构建响应
            if response.success:
                data = response.data
                logger.info("grpc_printer", f"打印机监控完成")

                return lumi_pilot_pb2.PrinterMonitorResponse(
                    success=True,
                    has_issues=data.get("has_issues", False),
                    issue=data.get("issue", ""),
                    suggestion=data.get("suggestion", ""),
                    confidence=data.get("confidence", "低"),
                    summary=data.get("summary", ""),
                    timestamp=data.get("timestamp", ""),
                    error=""
                )
            else:
                logger.error("grpc_printer", f"打印机监控失败: {response.error}")
                return lumi_pilot_pb2.PrinterMonitorResponse(
                    success=False,
                    has_issues=True,
                    issue="",
                    suggestion="",
                    confidence="低",
                    summary="",
                    timestamp="",
                    error=response.error or "未知错误"
                )

        except Exception as e:
            logger.error("grpc_printer", f"打印机监控请求处理失败: {str(e)}")
            return lumi_pilot_pb2.PrinterMonitorResponse(
                success=False,
                has_issues=True,
                issue="",
                suggestion="",
                confidence="低",
                summary="",
                timestamp="",
                error=f"服务内部错误: {str(e)}"
            )
