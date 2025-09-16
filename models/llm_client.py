"""
大语言模型客户端
使用LangChain调用OpenAI兼容的API
"""
import time
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from config.settings import get_settings
from utils.logger import get_logger

# 初始化模块logger
logger = get_logger(__name__)


class ChatResponse(BaseModel):
    """聊天响应数据模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class LLMClient:
    """
    大语言模型客户端
    负责与LangChain和OpenAI兼容的API进行交互
    """
    
    def __init__(self):
        """初始化LLM客户端"""
        self.settings = get_settings()
        self._client: Optional[ChatOpenAI] = None
        
        # 初始化客户端
        self._init_client()
    
    def _init_client(self) -> None:
        """初始化LangChain ChatOpenAI客户端"""
        try:
            self._client = ChatOpenAI(
                model=self.settings.openai_model,
                openai_api_key=self.settings.openai_api_key,
                openai_api_base=self.settings.openai_base_url,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
            )
            logger.info("llm_client", f"初始化成功: {self.settings.openai_model}")
        except Exception as e:
            logger.error("llm_client", f"初始化失败: {str(e)}")
            raise
    
    def chat(
        self, 
        message: str, 
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> ChatResponse:
        """
        发送聊天消息并获取响应
        
        Args:
            message: 用户输入的消息
            system_prompt: 可选的系统提示词
            **kwargs: 其他参数（如model, temperature, max_tokens等）
            
        Returns:
            ChatResponse: 包含响应结果的对象
        """
        if not self._client:
            return ChatResponse(
                success=False,
                message="",
                error="LLM客户端未初始化"
            )
        
        start_time = time.time()
        current_model = self.settings.openai_model  # 初始化默认模型
        
        try:
            # 准备消息列表
            messages = []
            
            # 添加系统消息（如果提供）
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            # 添加用户消息
            messages.append(HumanMessage(content=message))
            
            # 临时覆盖参数（如果提供）
            temp_client = self._client
            if kwargs:
                # 创建临时客户端以应用特定参数
                client_params = {
                    "model": kwargs.get("model", self.settings.openai_model),
                    "openai_api_key": self.settings.openai_api_key,
                    "openai_api_base": self.settings.openai_base_url,
                    "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                    "temperature": kwargs.get("temperature", self.settings.temperature),
                }
                temp_client = ChatOpenAI(**client_params)
                current_model = client_params["model"]
            
            # 调用API
            logger.info("llm_client", f"调用API: {current_model}")
            response = temp_client.invoke(messages)
            
            # 计算调用时长
            duration = time.time() - start_time
            
            # 提取响应内容
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # 记录API调用日志
            logger.info("llm_client", f"API调用成功: {current_model}, 耗时{duration:.2f}s")
            
            # 构建成功响应
            return ChatResponse(
                success=True,
                message=response_content,
                data={
                    "model": current_model,
                    "input_length": len(message),
                    "response_length": len(response_content),
                    "duration": duration,
                },
                metadata={
                    "timestamp": time.time(),
                    "system_prompt": system_prompt,
                    **kwargs
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"LLM API调用失败: {str(e)}"
            
            # 记录错误日志
            logger.error("llm_client", f"API调用失败: {str(e)}")
            
            return ChatResponse(
                success=False,
                message="",
                error=error_msg,
                metadata={
                    "timestamp": time.time(),
                    "duration": duration,
                }
            )
    
    def stream_chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ):
        """
        流式聊天（为未来扩展预留）
        
        Args:
            message: 用户输入的消息
            system_prompt: 可选的系统提示词
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应的每个部分
        """
        # 目前返回完整响应，后续可以实现真正的流式处理
        response = self.chat(message, system_prompt, **kwargs)
        if response.success:
            yield response.message
        else:
            yield f"错误: {response.error}"
    
    def validate_connection(self) -> bool:
        """
        验证与LLM服务的连接
        
        Returns:
            bool: 连接是否正常
        """
        try:
            test_response = self.chat("Hello", max_tokens=10)
            return test_response.success
        except Exception as e:
            logger.error("llm_client", f"连接验证失败: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取当前模型信息
        
        Returns:
            Dict[str, Any]: 模型配置信息
        """
        return {
            "model": self.settings.openai_model,
            "base_url": self.settings.openai_base_url,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            "client_initialized": self._client is not None,
        }