"""
简化的大语言模型客户端
使用标准MCP协议，通过原生HTTP客户端调用OpenAI兼容的API
"""
import time
import json
import uuid
from typing import Dict, Any, Optional, List

from pydantic import BaseModel

from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger
from infrastructure.mcp.client import MCPManager
from .openai_client import OpenAIClient, create_system_message, create_user_message, create_assistant_message, create_tool_message

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
    负责与OpenAI兼容的API进行交互，支持MCP工具调用
    """
    
    def __init__(self, mcp_manager: Optional[MCPManager] = None, debug: bool = True):
        """初始化LLM客户端"""
        self.settings = get_settings()
        self._client: Optional[OpenAIClient] = None
        self.mcp_manager = mcp_manager
        self.debug = debug
        
        # 初始化客户端
        self._init_client()
    
    def _debug_print(self, title: str, data: any):
        """打印调试信息"""
        if self.debug:
            print(f"\n{'='*60}")
            print(f"🔍 [LLM DEBUG] {title}")
            print(f"{'='*60}")
            if isinstance(data, (dict, list)):
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"{data}")
            print(f"{'='*60}")
    
    def _init_client(self) -> None:
        """初始化OpenAI HTTP客户端"""
        try:
            self._client = OpenAIClient(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
                model=self.settings.openai_model,
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
        request_id = str(uuid.uuid4())[:8]  # 生成8位request_id
        tool_start_time = None
        tool_end_time = None
        
        try:
            # 准备消息列表
            messages = []
            
            # 添加系统消息（如果提供）
            if system_prompt:
                messages.append(create_system_message(system_prompt))
            
            # 添加用户消息
            messages.append(create_user_message(message))
            
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
            
            # 准备调用参数
            call_params = {
                "model": kwargs.get("model", self.settings.openai_model),
                "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature),
            }
            current_model = call_params["model"]
            
            # 调用API
            logger.info("llm_client", f"调用API: {current_model}")
            
            # 打印发送给LLM的原始数据
            self._debug_print("发送给LLM的消息", [msg.content if hasattr(msg, 'content') else str(msg) for msg in messages])
            if tools:
                self._debug_print("发送给LLM的工具定义", tools)
            
            # 第一次调用LLM
            response = await self._client.chat_completion(
                messages=messages,
                tools=tools if tools else None,
                **call_params
            )
            
            # 打印从LLM接收的原始数据
            self._debug_print("从LLM接收的响应", {
                "content": response.content if hasattr(response, 'content') else str(response),
                "tool_calls": response.tool_calls if hasattr(response, 'tool_calls') else None,
                "response_type": type(response).__name__
            })
            
            # 检查是否有工具调用请求
            if tools and hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info("llm_client", f"LLM请求调用 {len(response.tool_calls)} 个工具")
                
                # 记录工具调用开始时间
                tool_start_time = time.time()
                
                # 处理工具调用
                tool_results = []
                for tool_call in response.tool_calls:
                    result = await self._execute_mcp_tool(tool_call)
                    tool_results.append(result)
                
                # 记录工具调用结束时间
                tool_end_time = time.time()
                
                # 构建包含工具结果的新对话
                conversation = messages.copy()
                # 添加助手的工具调用响应
                tool_calls_formatted = None
                if response.tool_calls:
                    tool_calls_formatted = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"])
                            }
                        }
                        for tc in response.tool_calls
                    ]
                assistant_msg = create_assistant_message(
                    content=response.content if response.content and response.content.strip() else "正在调用工具...",
                    tool_calls=tool_calls_formatted
                )
                conversation.append(assistant_msg)
                
                # 添加工具执行结果
                for i, result in enumerate(tool_results):
                    tool_call = response.tool_calls[i]
                    tool_msg = create_tool_message(
                        content=str(result),
                        tool_call_id=tool_call["id"]
                    )
                    conversation.append(tool_msg)
                
                # 让LLM基于工具结果生成最终回复
                logger.info("llm_client", "基于工具结果生成最终回复")
                self._debug_print("发送给LLM的完整对话（包含工具结果）", [
                    msg.content for msg in conversation
                ])
                response = await self._client.chat_completion(
                    messages=conversation,
                    **call_params
                )
                
                # 打印最终响应
                self._debug_print("从LLM接收的最终响应", {
                    "content": response.content if hasattr(response, 'content') else str(response),
                    "response_type": type(response).__name__
                })
            
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
                    # 可观测性字段
                    "request_id": request_id,
                    "tool_call_ids": [tc["id"] for tc in response.tool_calls] if hasattr(response, 'tool_calls') and response.tool_calls else [],
                    "llm_latency": duration,
                    "tool_latency": (tool_end_time - tool_start_time) if tool_start_time and tool_end_time else 0,
                    # 生成参数记录
                    "generation_params": {
                        "model": call_params["model"],
                        "temperature": call_params["temperature"],
                        "max_tokens": call_params["max_tokens"]
                    },
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
                    "request_id": request_id,
                    "llm_latency": duration,
                    "tool_latency": 0,
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
            # 从工具调用中提取信息
            tool_name = tool_call.get('name', '')
            tool_args = tool_call.get('args', {})
            
            logger.info("llm_client", f"执行MCP工具: {tool_name} 参数: {tool_args}")
            
            # 打印MCP工具调用的详细信息
            self._debug_print("MCP工具调用请求", {
                "tool_name": tool_name,
                "arguments": tool_args
            })
            
            if not tool_name:
                return "错误: 工具名称为空"
            
            # 通过MCP Manager调用工具
            if self.mcp_manager:
                result = await self.mcp_manager.call_tool(tool_name, tool_args)
                logger.info("llm_client", f"MCP工具调用成功: {tool_name} 结果: {result}")
                
                # 打印MCP工具调用的结果
                self._debug_print("MCP工具调用结果", {
                    "tool_name": tool_name,
                    "result": result
                })
                
                return str(result)
            else:
                return "抱歉，工具服务暂时不可用"
                
        except Exception as e:
            logger.error("llm_client", f"工具调用失败: {tool_name} - {str(e)}")
            # 友好降级处理
            friendly_messages = {
                "printer_status": "抱歉，打印机状态查询功能暂时不可用，请稍后重试或手动检查设备状态",
                "printer_print": "抱歉，打印功能暂时不可用，请稍后重试或联系技术支持"
            }
            return friendly_messages.get(tool_name, f"抱歉，{tool_name}功能暂时不可用，请稍后重试")
    
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