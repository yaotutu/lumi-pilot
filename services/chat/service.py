"""
聊天服务实现
基于现有ChatService重构为符合新架构的服务
"""
from typing import Dict, Any, Optional
from core.models import ServiceRequest, ServiceResponse, HealthStatus
from infrastructure.llm.client import LLMClient
from utils.personality import get_personality_manager
from .models import ChatRequest, ChatStreamRequest


class ChatService:
    """
    聊天服务类
    实现AI对话功能，符合新的服务协议
    """
    
    def __init__(self, llm_client: LLMClient, character: Optional[str] = None):
        """
        初始化聊天服务
        
        Args:
            llm_client: LLM客户端实例
            character: 使用的角色名称，如果为None则使用默认角色
        """
        self.llm_client = llm_client
        self.service_name = "chat"
        self.character = character
        self.personality_manager = get_personality_manager()
        
        # 确定系统提示词
        if self.character:
            self.system_prompt = self.personality_manager.get_system_prompt(self.character)
        else:
            self.system_prompt = """你是Lumi Pilot AI助手，一个智能、友好、专业的对话AI。
请用中文回复，保持回答简洁明了，准确有用。"""
    
    async def process(self, request: ServiceRequest) -> ServiceResponse:
        """
        处理聊天请求
        
        Args:
            request: 标准化服务请求
            
        Returns:
            ServiceResponse: 标准化服务响应
        """
        action = request.action
        request_id = request.context.request_id if request.context else "unknown"
        
        try:
            if action == "chat":
                return await self._handle_chat(request, request_id)
            elif action == "stream_chat":
                return await self._handle_stream_chat(request, request_id)
            else:
                return ServiceResponse.error_response(
                    error=f"不支持的操作: {action}",
                    service_name=self.service_name,
                    action=action,
                    request_id=request_id
                )
        except Exception as e:
            return ServiceResponse.error_response(
                error=f"处理失败: {str(e)}",
                service_name=self.service_name,
                action=action,
                request_id=request_id
            )
    
    async def _handle_chat(self, request: ServiceRequest, request_id: str) -> ServiceResponse:
        """
        处理普通聊天请求
        
        Args:
            request: 服务请求
            request_id: 请求ID
            
        Returns:
            ServiceResponse: 服务响应
        """
        # 解析聊天请求
        chat_req = ChatRequest(**request.payload)
        
        # 验证输入
        if not chat_req.message or not chat_req.message.strip():
            return ServiceResponse.error_response(
                error="消息内容不能为空",
                service_name=self.service_name,
                action="chat",
                request_id=request_id
            )
        
        # 准备LLM参数
        llm_kwargs = {}
        if chat_req.temperature is not None:
            llm_kwargs['temperature'] = chat_req.temperature
        if chat_req.max_tokens is not None:
            llm_kwargs['max_tokens'] = chat_req.max_tokens
        
        # 调用LLM
        chat_response = await self.llm_client.chat(
            message=chat_req.message,
            system_prompt=self.system_prompt,
            **llm_kwargs
        )
        
        if chat_response.success:
            response_data = {
                "message": chat_response.message,
                "model": chat_response.data.get("model"),
                "input_length": chat_response.data.get("input_length"),
                "response_length": chat_response.data.get("response_length")
            }
            
            return ServiceResponse.success_response(
                data=response_data,
                service_name=self.service_name,
                action="chat",
                request_id=request_id
            )
        else:
            return ServiceResponse.error_response(
                error=chat_response.error or "未知错误",
                service_name=self.service_name,
                action="chat",
                request_id=request_id
            )
    
    async def _handle_stream_chat(self, request: ServiceRequest, request_id: str) -> ServiceResponse:
        """
        处理流式聊天请求（暂时返回普通响应）
        
        Args:
            request: 服务请求
            request_id: 请求ID
            
        Returns:
            ServiceResponse: 服务响应
        """
        # 暂时使用普通聊天处理，后续可以实现真正的流式处理
        return await self._handle_chat(request, request_id)
    
    async def health_check(self) -> HealthStatus:
        """
        检查聊天服务健康状态
        
        Returns:
            HealthStatus: 健康状态信息
        """
        try:
            # 检查LLM连接
            llm_healthy = await self.llm_client.validate_connection()
            model_info = self.llm_client.get_model_info()
            
            # 检查角色管理器状态
            available_characters = self.personality_manager.list_available_characters()
            
            return HealthStatus(
                healthy=llm_healthy,
                service_name=self.service_name,
                details={
                    "llm_connected": llm_healthy,
                    "model_info": model_info,
                    "system_prompt_configured": True,
                    "available_characters": available_characters,
                    "characters_count": len(available_characters)
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
        return ["chat", "stream_chat"]