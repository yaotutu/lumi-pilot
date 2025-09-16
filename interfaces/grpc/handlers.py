"""
gRPC服务处理器
实现简化的Lumi Pilot gRPC接口
"""
import asyncio

import grpc

from core.application import Application
from core.models import ServiceRequest
from infrastructure.logging import get_logger
from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc

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
        logger.info("grpc_chat", f"收到对话请求: {request.message[:50]}...")
        
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
                return lumi_pilot_pb2.ChatResponse(
                    success=True,
                    message=response.data.get("message", ""),
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