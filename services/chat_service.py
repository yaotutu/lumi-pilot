"""
聊天服务模块
提供高层次的聊天功能和业务逻辑
"""
from typing import Dict, Any, Optional

from models.llm_client import LLMClient, ChatResponse
from utils.logger import get_logger
from utils.personality import get_personality_manager
from config.settings import get_settings

# 初始化模块logger
logger = get_logger(__name__)


class ChatService:
    """
    聊天服务类
    提供聊天功能的业务逻辑层
    """
    
    def __init__(self):
        """初始化聊天服务"""
        self.settings = get_settings()
        self.llm_client = LLMClient()
        self.personality_manager = get_personality_manager()
        
        # 默认系统提示词（当没有指定人物时使用）
        self.default_system_prompt = """你是Lumi Pilot AI助手，一个智能、友好、专业的对话AI。
请用中文回复，保持回答简洁明了，准确有用。"""
    
    def process_message(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        character: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        处理用户消息并返回结构化响应
        
        Args:
            user_input: 用户输入
            system_prompt: 自定义系统提示词
            character: 人物名称
            context: 对话上下文信息
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 标准化的JSON响应
        """
        logger.info("chat_service", f"处理消息: {user_input[:20]}{'...' if len(user_input) > 20 else ''}")
        
        # 输入验证
        if not user_input or not user_input.strip():
            return self._create_error_response("输入不能为空")
        
        # 确定系统提示词：优先级为 system_prompt > character > default
        if system_prompt:
            effective_system_prompt = system_prompt
        elif character:
            effective_system_prompt = self.personality_manager.get_system_prompt(character)
        else:
            effective_system_prompt = self.default_system_prompt
        
        # 如果有上下文，可以在这里处理上下文信息
        # 目前暂不实现上下文管理，后续可扩展
        
        try:
            # 调用LLM
            chat_response = self.llm_client.chat(
                message=user_input,
                system_prompt=effective_system_prompt,
                **kwargs
            )
            
            if chat_response.success:
                return self._create_success_response(
                    message=chat_response.message,
                    data=chat_response.data,
                    metadata=chat_response.metadata
                )
            else:
                return self._create_error_response(
                    chat_response.error or "未知错误",
                    metadata=chat_response.metadata
                )
                
        except Exception as e:
            logger.error("chat_service", f"处理失败: {str(e)}")
            return self._create_error_response(f"处理失败: {str(e)}")
    
    def _create_success_response(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建成功响应"""
        return {
            "status": "success",
            "code": 200,
            "message": message,
            "data": data or {},
            "metadata": {
                "app_name": self.settings.app_name,
                "version": "0.1.0",
                **(metadata or {})
            }
        }
    
    def _create_error_response(
        self,
        error_message: str,
        code: int = 500,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "status": "error",
            "code": code,
            "message": "",
            "error": error_message,
            "data": {},
            "metadata": {
                "app_name": self.settings.app_name,
                "version": "0.1.0",
                **(metadata or {})
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            # 检查LLM连接
            llm_status = self.llm_client.validate_connection()
            model_info = self.llm_client.get_model_info()
            
            return {
                "status": "healthy" if llm_status else "unhealthy",
                "code": 200 if llm_status else 503,
                "message": "服务正常" if llm_status else "LLM服务连接失败",
                "data": {
                    "llm_connected": llm_status,
                    "model_info": model_info,
                },
                "metadata": {
                    "app_name": self.settings.app_name,
                    "version": "0.1.0",
                    "check_time": __import__('time').time()
                }
            }
        except Exception as e:
            logger.error("chat_service", f"健康检查失败: {str(e)}")
            return self._create_error_response(f"健康检查失败: {str(e)}", code=503)