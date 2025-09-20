"""
MCP服务器模块
按分类组织的内部MCP服务器实现
"""
from .basic import register_basic_tools
from .internal import create_internal_mcp_server
from .models import GreetingResponse, ServerInfo
from .printer import register_printer_tools
from .system import register_system_tools
from .tools import register_all_tools
from .utility import register_utility_tools

__all__ = [
    "create_internal_mcp_server",
    "register_all_tools",
    "register_basic_tools",
    "register_system_tools",
    "register_utility_tools",
    "register_printer_tools",
    "ServerInfo",
    "GreetingResponse",
]
