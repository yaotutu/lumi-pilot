"""
内部MCP服务器
使用FastMCP创建内存中的MCP服务器，采用最佳实践架构
"""
from fastmcp import FastMCP

from infrastructure.logging.logger import get_logger

from .tools import register_all_tools

logger = get_logger(__name__)


def create_internal_mcp_server() -> FastMCP:
    """
    创建内部MCP服务器实例

    Returns:
        FastMCP: 配置好的内部MCP服务器
    """
    # 创建内存中的MCP服务器
    mcp = FastMCP(
        name="Lumi Pilot Internal Server",
        instructions="""
        Lumi Pilot内部MCP服务器，提供基础功能和系统工具。
        支持问候、回显、时间查询、系统信息和数学计算等功能。
        """
    )

    # 注册工具（按分类）
    register_all_tools(mcp)

    # 添加配置资源
    @mcp.resource("config://server")
    def get_server_config() -> dict:
        """获取服务器配置资源"""
        return {
            "name": "Lumi Pilot Internal Server",
            "mode": "internal",
            "transport": "in-memory",
            "version": "1.0.0",
            "created_by": "Lumi Pilot"
        }

    logger.info("internal_mcp", "内部MCP服务器创建完成")
    return mcp
