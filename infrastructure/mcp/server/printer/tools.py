"""
打印机工具注册
"""
from fastmcp import FastMCP
from infrastructure.logging.logger import get_logger
from .handlers import get_printer_status, print_document, get_print_queue, get_printer_progress

logger = get_logger(__name__)


def register_printer_tools(mcp: FastMCP) -> int:
    """注册打印机工具"""
    logger.info("printer_tools", "注册打印机工具")
    
    @mcp.tool
    def printer_status() -> dict:
        """获取打印机状态 - 通过API调用真实的打印机状态接口"""
        return get_printer_status()
    
    @mcp.tool
    def printer_print(content: str, printer_name: str = "default") -> str:
        """打印文档 - 发送文档到指定打印机进行打印"""
        return print_document(content, printer_name)
    
    @mcp.tool
    def printer_queue() -> dict:
        """获取打印队列状态 - 查看当前打印任务队列"""
        return get_print_queue()
    
    @mcp.tool
    def printer_progress(job_id: str) -> dict:
        """获取打印进度 - 通过SSE获取指定任务的打印进度"""
        return get_printer_progress(job_id)
    
    logger.info("printer_tools", "打印机工具注册完成")
    return 4