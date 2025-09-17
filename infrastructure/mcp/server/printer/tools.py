"""
打印机工具注册
"""
from fastmcp import FastMCP
from infrastructure.logging.logger import get_logger
from .handlers import PrinterHandlers

logger = get_logger(__name__)


def register_printer_tools(mcp: FastMCP) -> int:
    """注册打印机工具"""
    logger.info("printer_tools", "注册打印机工具")
    
    @mcp.tool
    def get_printer_status() -> dict:
        """获取打印机状态"""
        return PrinterHandlers.get_printer_status()
    
    @mcp.tool
    def print_document(content: str, printer_name: str = "default") -> str:
        """打印文档"""
        return PrinterHandlers.print_document(content, printer_name)
    
    logger.info("printer_tools", "打印机工具注册完成")
    return 2