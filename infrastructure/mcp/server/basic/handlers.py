"""
基础交互工具处理器
"""
from datetime import datetime

from infrastructure.logging.logger import get_logger

from ..models import GreetingResponse

logger = get_logger(__name__)


class BasicHandlers:
    """基础交互工具处理器"""

    @staticmethod
    def handle_greeting(name: str = "World") -> str:
        """处理问候请求"""
        logger.info("basic_handlers", f"处理问候请求: name={name}")

        response = GreetingResponse(
            message=f"Hello, {name}! 这是来自Lumi Pilot内部MCP服务器的问候。",
            timestamp=datetime.now().isoformat(),
            source="Lumi Pilot Internal Server"
        )

        result = response.to_string()
        logger.info("basic_handlers", f"返回问候消息: {result}")
        return result

    @staticmethod
    def handle_echo(message: str) -> str:
        """处理回显请求"""
        logger.info("basic_handlers", f"处理回显请求: {message}")
        result = f"Echo: {message}"
        logger.info("basic_handlers", f"回显结果: {result}")
        return result
