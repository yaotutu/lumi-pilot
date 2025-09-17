"""
系统信息工具注册
"""
from fastmcp import FastMCP
from infrastructure.logging.logger import get_logger
from .handlers import SystemHandlers

logger = get_logger(__name__)


def register_system_tools(mcp: FastMCP) -> int:
    """注册系统信息工具"""
    logger.info("system_tools", "注册系统信息工具")
    
    @mcp.tool
    def get_server_info() -> dict:
        """获取服务器信息"""
        return SystemHandlers.get_server_info()
    
    @mcp.tool
    def get_current_time() -> str:
        """获取当前时间"""
        return SystemHandlers.get_current_time()
    
    @mcp.tool
    def get_system_info() -> dict:
        """获取系统信息"""
        return SystemHandlers.get_system_info()
    
    logger.info("system_tools", "系统信息工具注册完成")
    return 3