"""
gRPC服务处理器
实现gRPC服务接口，复用现有的应用架构
"""
import asyncio
from typing import Iterator

import grpc

from core.application import Application
from core.models import ServiceRequest
from infrastructure.logging import get_logger
from .generated import chat_pb2, chat_pb2_grpc

# 初始化模块logger
logger = get_logger(__name__)


class ChatServiceHandler(chat_pb2_grpc.ChatServiceServicer):
    """
    gRPC聊天服务处理器
    将gRPC请求转换为统一的服务请求，并返回gRPC响应
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
    
    def Chat(self, request: chat_pb2.ChatRequest, context: grpc.ServicerContext) -> chat_pb2.ChatResponse:
        """
        处理gRPC聊天请求
        
        Args:
            request: gRPC聊天请求
            context: gRPC服务上下文
            
        Returns:
            chat_pb2.ChatResponse: gRPC聊天响应
        """
        logger.info("grpc_chat", f"收到gRPC聊天请求: {request.message[:50]}...")
        
        try:
            # 将gRPC请求转换为统一的服务请求
            service_request = self._convert_to_service_request(request)
            
            # 使用异步方式调用服务
            response = self.loop.run_until_complete(
                self.application.execute("chat", service_request)
            )
            
            # 将服务响应转换为gRPC响应
            return self._convert_to_grpc_response(response)
            
        except Exception as e:
            logger.error("grpc_chat", f"gRPC聊天请求处理失败: {str(e)}")
            return chat_pb2.ChatResponse(
                success=False,
                message="",
                error=f"服务内部错误: {str(e)}",
                metadata=chat_pb2.ChatMetadata(
                    request_id="error",
                    timestamp=str(__import__('time').time())
                )
            )
    
    def StreamChat(self, request: chat_pb2.ChatRequest, context: grpc.ServicerContext) -> Iterator[chat_pb2.ChatStreamResponse]:
        """
        处理流式gRPC聊天请求
        暂时实现为非流式响应
        
        Args:
            request: gRPC聊天请求
            context: gRPC服务上下文
            
        Yields:
            chat_pb2.ChatStreamResponse: 流式响应片段
        """
        logger.info("grpc_stream_chat", f"收到gRPC流式聊天请求: {request.message[:50]}...")
        
        try:
            # 调用普通聊天获取完整响应
            chat_response = self.Chat(request, context)
            
            if chat_response.success:
                # 将完整响应作为单个流式片段返回
                yield chat_pb2.ChatStreamResponse(
                    chunk=chat_response.message,
                    is_final=True,
                    metadata=chat_response.metadata
                )
            else:
                # 返回错误流式响应
                yield chat_pb2.ChatStreamResponse(
                    chunk=f"错误: {chat_response.error}",
                    is_final=True,
                    metadata=chat_response.metadata
                )
                
        except Exception as e:
            logger.error("grpc_stream_chat", f"gRPC流式聊天请求处理失败: {str(e)}")
            yield chat_pb2.ChatStreamResponse(
                chunk=f"服务内部错误: {str(e)}",
                is_final=True,
                metadata=chat_pb2.ChatMetadata(
                    request_id="error",
                    timestamp=str(__import__('time').time())
                )
            )
    
    def _convert_to_service_request(self, grpc_request: chat_pb2.ChatRequest) -> ServiceRequest:
        """
        将gRPC请求转换为统一的服务请求
        
        Args:
            grpc_request: gRPC请求
            
        Returns:
            ServiceRequest: 统一的服务请求
        """
        payload = {
            "message": grpc_request.message
        }
        
        # 添加可选参数
        if grpc_request.HasField("system_prompt"):
            payload["system_prompt"] = grpc_request.system_prompt
        
        if grpc_request.HasField("character"):
            payload["character"] = grpc_request.character
        
        if grpc_request.HasField("temperature"):
            payload["temperature"] = grpc_request.temperature
        
        if grpc_request.HasField("max_tokens"):
            payload["max_tokens"] = grpc_request.max_tokens
        
        return ServiceRequest(
            action="chat",
            payload=payload
        )
    
    def _convert_to_grpc_response(self, service_response) -> chat_pb2.ChatResponse:
        """
        将服务响应转换为gRPC响应
        
        Args:
            service_response: 统一的服务响应
            
        Returns:
            chat_pb2.ChatResponse: gRPC响应
        """
        if service_response.success:
            # 成功响应
            metadata = chat_pb2.ChatMetadata(
                request_id=service_response.metadata.request_id,
                model=service_response.data.get("model", ""),
                input_length=service_response.data.get("input_length", 0),
                response_length=service_response.data.get("response_length", 0),
                duration=service_response.metadata.duration or 0.0,
                timestamp=service_response.metadata.timestamp.isoformat()
            )
            
            return chat_pb2.ChatResponse(
                success=True,
                message=service_response.data.get("message", ""),
                error="",
                metadata=metadata
            )
        else:
            # 错误响应
            metadata = chat_pb2.ChatMetadata(
                request_id=service_response.metadata.request_id,
                duration=service_response.metadata.duration or 0.0,
                timestamp=service_response.metadata.timestamp.isoformat()
            )
            
            return chat_pb2.ChatResponse(
                success=False,
                message="",
                error=service_response.error or "未知错误",
                metadata=metadata
            )