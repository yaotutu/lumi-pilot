"""
打印机工具注册
"""
from fastmcp import FastMCP

from infrastructure.logging.logger import get_logger

from .handlers import get_printer_handler

logger = get_logger(__name__)


def register_printer_tools(mcp: FastMCP) -> int:
    """注册打印机工具"""
    logger.info("printer_tools", "注册打印机工具")

    # 计数器，记录注册的工具数量
    registered_count = 0

    @mcp.tool
    async def printer_status(include_temperature: bool = True) -> dict:
        """
        获取打印机状态 - 通过API调用真实的打印机状态接口

        Args:
            include_temperature: 是否包含温度信息，默认true
        """
        handler = get_printer_handler()
        return await handler.get_printer_status()
    registered_count = registered_count + 1

    @mcp.tool
    async def printer_set_nozzle_temperature(temperature: float) -> dict:
        """
        设置喷嘴温度 - 通过API设置打印机喷嘴目标温度

        Args:
            temperature: 目标温度值（摄氏度），范围0-500
        """
        handler = get_printer_handler()
        result = await handler.set_nozzle_temperature(temperature)
        return result
    registered_count = registered_count + 1

    @mcp.tool
    async def printer_set_bed_temperature(temperature: float) -> dict:
        """
        设置热床温度 - 通过API设置打印机热床目标温度

        Args:
            temperature: 目标温度值（摄氏度），范围0-150
        """
        handler = get_printer_handler()
        result = await handler.set_bed_temperature(temperature)
        return result
    registered_count = registered_count + 1

    # @mcp.tool
    # async def printer_print(content: str, printer_name: str = "default") -> str:
    #     """打印文档 - 发送文档到指定打印机进行打印"""
    #     handler = get_printer_handler()
    #     return await handler.print_document(content, printer_name)
    # registered_count = registered_count + 1

    # @mcp.tool
    # def printer_queue() -> dict:
    #     """获取打印队列状态 - 查看当前打印任务队列"""
    #     return get_print_queue()
    # registered_count = registered_count + 1

    # @mcp.tool
    # def printer_progress(job_id: str) -> dict:
    #     """获取打印进度 - 通过SSE获取指定任务的打印进度"""
    #     return get_printer_progress(job_id)
    # registered_count = registered_count + 1

    logger.info("printer_tools", "打印机工具注册完成")
    return registered_count
