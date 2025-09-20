"""
MCP工具统一注册
集成所有分类的工具注册功能
"""
from fastmcp import FastMCP

from infrastructure.logging.logger import get_logger

from .printer import register_printer_tools

logger = get_logger(__name__)


def register_all_tools(mcp: FastMCP) -> int:
    """注册所有分类的工具"""
    logger.info("mcp_tools", "开始注册所有分类工具")

    # 注册各分类工具，获取每类的工具数量
    # basic_count = register_basic_tools(mcp)
    # system_count = register_system_tools(mcp)
    # utility_count = register_utility_tools(mcp)
    printer_count = register_printer_tools(mcp)

    # 计算总工具数量
    # total_tools = basic_count + system_count + utility_count + printer_count
    total_tools = printer_count

    logger.info("mcp_tools", f"所有分类工具注册完成，共 {total_tools} 个工具")
    return total_tools
