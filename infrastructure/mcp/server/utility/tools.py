"""
实用工具注册
"""
from fastmcp import FastMCP
from infrastructure.logging.logger import get_logger
from .handlers import UtilityHandlers

logger = get_logger(__name__)


def register_utility_tools(mcp: FastMCP) -> int:
    """注册实用工具"""
    logger.info("utility_tools", "注册实用工具")
    
    @mcp.tool
    def calculate(expression: str) -> str:
        """数学计算工具 - 安全计算数学表达式"""
        return UtilityHandlers.calculate_math(expression)
    
    logger.info("utility_tools", "实用工具注册完成")
    return 1