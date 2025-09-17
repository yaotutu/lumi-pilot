"""
内部MCP服务器
使用FastMCP创建内存中的MCP服务器，避免外部进程通信问题
"""
from fastmcp import FastMCP
from infrastructure.logging.logger import get_logger

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
        这是Lumi Pilot内部的MCP服务器，提供基本的测试工具。
        可以调用hello_world工具来测试MCP集成。
        """
    )
    
    @mcp.tool
    def hello_world(name: str = "World") -> str:
        """
        返回Hello World消息的简单测试工具
        
        Args:
            name: 要问候的名字，默认为"World"
            
        Returns:
            问候消息
        """
        logger.info("internal_mcp", f"调用hello_world工具，参数: name={name}")
        message = f"Hello, {name}! 这是来自Lumi Pilot内部MCP服务器的问候。"
        logger.info("internal_mcp", f"返回消息: {message}")
        return message
    
    @mcp.tool  
    def get_server_info() -> dict:
        """
        获取服务器信息
        
        Returns:
            服务器信息字典
        """
        logger.info("internal_mcp", "调用get_server_info工具")
        info = {
            "server_name": "Lumi Pilot Internal Server",
            "version": "1.0.0",
            "type": "internal",
            "status": "running",
            "tools_count": 2
        }
        logger.info("internal_mcp", f"返回服务器信息: {info}")
        return info
    
    @mcp.resource("config://server")
    def get_server_config() -> dict:
        """
        获取服务器配置资源
        
        Returns:
            服务器配置
        """
        return {
            "name": "Lumi Pilot Internal Server",
            "mode": "internal",
            "transport": "in-memory",
            "created_by": "Lumi Pilot"
        }
    
    logger.info("internal_mcp", "内部MCP服务器创建成功")
    return mcp