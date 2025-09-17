"""
基础交互工具注册
"""
from fastmcp import FastMCP
from infrastructure.logging.logger import get_logger
from .handlers import BasicHandlers

logger = get_logger(__name__)


def register_basic_tools(mcp: FastMCP) -> int:
    """注册基础交互工具"""
    logger.info("basic_tools", "注册基础交互工具")
    
    @mcp.tool
    def hello_world(name: str = "World") -> str:
        """问候工具 - 返回友好的问候消息"""
        return BasicHandlers.handle_greeting(name)
    
    @mcp.tool
    def echo(message: str) -> str:
        """回显工具 - 返回输入的消息"""
        return BasicHandlers.handle_echo(message)
    
    logger.info("basic_tools", "基础交互工具注册完成")
    return 2