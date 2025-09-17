"""
MCP工厂模块
提供MCP组件的初始化和配置功能
"""
from infrastructure.logging.logger import get_logger
from .client import MCPManager

logger = get_logger(__name__)


class MCPFactory:
    """MCP组件工厂"""
    
    @staticmethod
    async def create_with_default_config() -> MCPManager:
        """
        创建配置了内部服务器的MCP管理器
        
        Returns:
            初始化完成的MCPManager实例
        """
        try:
            logger.info("mcp_factory", "创建内部MCP服务器管理器")
            
            # 创建MCP管理器
            mcp_manager = MCPManager()
            
            # 初始化内部服务器
            await mcp_manager.connect_all()
            
            # 输出服务器信息
            server_info = mcp_manager.get_server_info()
            logger.info("mcp_factory", 
                       f"MCP管理器初始化完成，连接了 {len(server_info['connected_servers'])} 个服务器")
            logger.info("mcp_factory", f"可用工具总数: {server_info['total_tools']}")
            
            return mcp_manager
            
        except Exception as e:
            logger.error("mcp_factory", f"创建MCP管理器失败: {e}")
            raise