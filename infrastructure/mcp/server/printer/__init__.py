"""
打印机工具
提供打印机状态查询和文档打印功能
"""
from .handlers import PrinterHandlers
from .tools import register_printer_tools

__all__ = [
    "PrinterHandlers",
    "register_printer_tools",
]