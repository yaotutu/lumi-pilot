"""
简化的大语言模型客户端
使用标准MCP协议，通过LangChain调用OpenAI兼容的API
"""
import time
import json
from typing import Dict, Any, Optional, List

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger
from infrastructure.mcp.client import MCPManager

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
    负责与LangChain和OpenAI兼容的API进行交互，支持MCP工具调用
    """
    
    def __init__(self, mcp_manager: Optional[MCPManager] = None):
        """初始化LLM客户端"""
        self.settings = get_settings()
        self._client: Optional[ChatOpenAI] = None
        self.mcp_manager = mcp_manager
        
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
    
    async def chat(
        self, 
        message: str, 
        system_prompt: Optional[str] = None,
        enable_tools: bool = True,
        **kwargs: Any
    ) -> ChatResponse:
        """
        发送聊天消息并获取响应
        
        Args:
            message: 用户输入的消息
            system_prompt: 可选的系统提示词
            enable_tools: 是否启用MCP工具调用
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
        current_model = self.settings.openai_model
        
        try:
            # 准备消息列表
            messages = []
            
            # 添加系统消息（如果提供）
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            # 添加用户消息
            messages.append(HumanMessage(content=message))
            
            # 获取MCP工具定义
            tools = []
            if enable_tools and self.mcp_manager:
                tools = self.mcp_manager.get_tools_for_llm()
                if tools:
                    logger.info("llm_client", f"启用 {len(tools)} 个MCP工具")
                    for tool in tools:
                        tool_name = tool["function"]["name"]
                        tool_desc = tool["function"]["description"]
                        logger.info("llm_client", f"可用工具: {tool_name} - {tool_desc}")
            
            # 临时覆盖参数（如果提供）
            temp_client = self._client
            if kwargs:
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
            
            # 第一次调用LLM
            if tools:
                response = temp_client.invoke(messages, tools=tools)
            else:
                response = temp_client.invoke(messages)
            
            # 检查是否有工具调用请求
            if tools and hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info("llm_client", f"LLM请求调用 {len(response.tool_calls)} 个工具")
                
                # 处理工具调用
                tool_results = []
                for tool_call in response.tool_calls:
                    result = await self._execute_mcp_tool(tool_call)
                    tool_results.append(result)
                
                # 构建包含工具结果的新对话
                conversation = messages.copy()
                conversation.append(response)
                
                # 添加工具结果
                for i, result in enumerate(tool_results):
                    tool_name = response.tool_calls[i].get('name', 'unknown')
                    tool_result_msg = f"工具 {tool_name} 执行结果: {result}"
                    conversation.append(HumanMessage(content=tool_result_msg))
                
                # 让LLM基于工具结果生成最终回复
                logger.info("llm_client", "基于工具结果生成最终回复")
                response = temp_client.invoke(conversation)
            
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
                    "tools_used": len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0,
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
    
    async def _execute_mcp_tool(self, tool_call: Dict[str, Any]) -> str:
        """
        执行MCP工具调用（使用标准MCP协议）
        
        Args:
            tool_call: LangChain工具调用对象
            
        Returns:
            工具执行结果
        """
        try:
            # 从LangChain工具调用中提取信息
            tool_name = tool_call.get('name', '')
            tool_args = tool_call.get('args', {})
            
            logger.info("llm_client", f"执行MCP工具: {tool_name} 参数: {tool_args}")
            
            if not tool_name:
                return "错误: 工具名称为空"
            
            # 通过MCP Manager调用工具
            if self.mcp_manager:
                result = await self.mcp_manager.call_tool(tool_name, tool_args)
                logger.info("llm_client", f"MCP工具调用成功: {tool_name} 结果: {result}")
                return str(result)
            else:
                return "错误: MCP管理器未初始化"
                
        except Exception as e:
            error_msg = f"MCP工具调用失败: {str(e)}"
            logger.error("llm_client", error_msg)
            return error_msg
    
    async def validate_connection(self) -> bool:
        """
        验证与LLM服务的连接
        
        Returns:
            bool: 连接是否正常
        """
        try:
            test_response = await self.chat("Hello", max_tokens=10)
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
        mcp_info = {}
        if self.mcp_manager:
            mcp_info = {
                "mcp_enabled": True,
                "mcp_servers": self.mcp_manager.get_server_info()
            }
        else:
            mcp_info = {"mcp_enabled": False}
            
        return {
            "model": self.settings.openai_model,
            "base_url": self.settings.openai_base_url,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            "client_initialized": self._client is not None,
            **mcp_info
        }