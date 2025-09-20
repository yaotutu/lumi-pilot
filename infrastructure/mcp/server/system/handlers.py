"""
系统信息工具处理器
"""
import os
import platform
from datetime import datetime

from infrastructure.logging.logger import get_logger

from ..models import ServerInfo

logger = get_logger(__name__)


class SystemHandlers:
    """系统信息工具处理器"""

    @staticmethod
    def get_server_info() -> dict:
        """获取服务器信息"""
        logger.info("system_handlers", "获取服务器信息")

        server_info = ServerInfo(
            server_name="Lumi Pilot Internal Server",
            version="1.0.0",
            type="内部MCP服务器",
            status="运行中",
            tools_count=8,
            description="Lumi Pilot项目的内部MCP服务器"
        )

        result = server_info.to_dict()
        logger.info("system_handlers", f"返回服务器信息: {result}")
        return result

    @staticmethod
    def get_current_time() -> str:
        """获取当前时间"""
        logger.info("system_handlers", "获取当前时间")
        current_time = datetime.now().isoformat()
        logger.info("system_handlers", f"当前时间: {current_time}")
        return current_time

    @staticmethod
    def get_system_info() -> dict:
        """获取系统信息"""
        logger.info("system_handlers", "获取系统信息")

        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "current_directory": os.getcwd()
        }

        logger.info("system_handlers", f"系统信息: {system_info}")
        return system_info
