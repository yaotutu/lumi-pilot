"""
MCP客户端实现
基于FastMCP库提供统一的MCP服务器连接和工具调用功能
"""
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from fastmcp import Client
from infrastructure.logging.logger import get_logger
from ..server import create_internal_mcp_server

logger = get_logger(__name__)


@dataclass 
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str


class MCPManager:
    """
    MCP连接管理器
    负责管理多个MCP服务器连接和工具调用
    """
    
    def __init__(self):
        self.clients: Dict[str, Client] = {}
        self.tools: Dict[str, MCPTool] = {}  # tool_name -> MCPTool
    
    
    async def connect_all(self) -> None:
        """初始化内部MCP服务器"""
        await self._add_internal_server()
    
    async def _add_internal_server(self) -> None:
        """添加内部MCP服务器"""
        try:
            logger.info("mcp_manager", "初始化内部MCP服务器...")
            
            # 创建内部MCP服务器
            internal_server = create_internal_mcp_server()
            
            # 创建内存中的客户端连接
            client = Client(internal_server)
            server_name = "internal"
            
            # 保存客户端
            self.clients[server_name] = client
            logger.info("mcp_manager", f"内部MCP服务器客户端创建成功")
            
            # 注册工具
            await self._register_tools(server_name, client)
            
            logger.info("mcp_manager", f"内部MCP服务器初始化完成")
            
        except Exception as e:
            logger.error("mcp_manager", f"内部MCP服务器初始化失败: {e}")
            raise
    
    async def _register_tools(self, server_name: str, client: Client) -> None:
        """从MCP服务器注册工具"""
        try:
            # 使用async with context manager来管理连接
            async with client:
                # 获取工具列表（FastMCP直接返回工具列表，不是包装对象）
                tools_list = await client.list_tools()
                
                for tool in tools_list:
                    tool_key = f"{server_name}:{tool.name}"
                    
                    mcp_tool = MCPTool(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.inputSchema,
                        server_name=server_name
                    )
                    
                    self.tools[tool_key] = mcp_tool
                    
                    logger.info("mcp_manager", 
                              f"注册工具: {tool.name} (来自服务器 {server_name})")
                
        except Exception as e:
            logger.error("mcp_manager", f"注册工具失败 (服务器 {server_name}): {e}")
    
    def get_all_tools(self) -> List[MCPTool]:
        """获取所有可用工具"""
        return list(self.tools.values())
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取适用于LLM的工具定义格式
        转换为OpenAI函数调用格式
        """
        llm_tools = []
        
        for tool in self.tools.values():
            llm_tool = {
                "type": "function",
                "function": {
                    "name": f"{tool.server_name}:{tool.name}",
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            llm_tools.append(llm_tool)
        
        return llm_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        调用MCP工具
        
        Args:
            tool_name: 工具名称，格式为 "server_name:tool_name"
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = self.tools[tool_name]
        client = self.clients.get(tool.server_name)
        
        if not client:
            raise ValueError(f"服务器连接不存在: {tool.server_name}")
        
        try:
            logger.info("mcp_manager", f"调用工具: {tool_name} 参数: {arguments}")
            
            # 使用async with context manager来管理连接
            async with client:
                # 调用MCP工具
                result = await client.call_tool(tool.name, arguments)
                
                logger.info("mcp_manager", f"工具调用成功: {tool_name}")
                
                # 返回结果内容（FastMCP返回的是带有content的对象）
                if hasattr(result, 'content') and result.content:
                    return result.content[0].text if result.content[0].text else str(result.content[0])
                else:
                    return str(result)
            
        except Exception as e:
            logger.error("mcp_manager", f"工具调用失败: {tool_name} 错误: {e}")
            raise
    
    async def disconnect_all(self) -> None:
        """断开所有MCP服务器连接"""
        # FastMCP客户端使用context manager自动管理连接
        # 这里只需要清理内部状态
        self.clients.clear()
        self.tools.clear()
        logger.info("mcp_manager", "已清理所有MCP客户端连接")
    
    def health_check(self) -> Dict[str, bool]:
        """检查所有MCP服务器连接状态"""
        health = {}
        for name, client in self.clients.items():
            # 简单检查客户端是否存在
            health[name] = client is not None
        return health
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "connected_servers": list(self.clients.keys()),
            "total_tools": len(self.tools),
            "tools_by_server": {
                server: len([t for t in self.tools.values() if t.server_name == server])
                for server in self.clients.keys()
            }
        }