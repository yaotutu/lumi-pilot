"""
打印机工具处理器
"""
import asyncio

from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger

from .client import PrinterAPIClient

logger = get_logger(__name__)


class PrinterHandlers:
    """打印机工具处理器"""

    def __init__(self, base_url: str = None):
        """初始化打印机处理器"""
        settings = get_settings()

        # 使用配置文件中的设置，如果没有传入参数的话
        if base_url is None:
            base_url = settings.printer.base_url

        self.client = PrinterAPIClient(
            base_url=base_url,
            timeout=settings.printer.timeout,
            debug=settings.printer.debug
        )
        self.settings = settings

    async def get_printer_status(self) -> dict:
        """获取打印机状态"""
        logger.info("printer_handlers", "获取打印机状态")

        try:
            # 调用打印机状态API（SSE接口）
            status_endpoint = self.settings.printer.endpoints.status
            status_data = await self.client.get_sse_with_field(
                status_endpoint, "state"
            )
            logger.info("printer_handlers", f"打印机状态获取成功: {status_data}")
            return status_data

        except Exception as e:
            # 如果API调用失败，返回错误信息
            error_msg = f"获取打印机状态失败: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return {
                "error": error_msg,
                "status": "离线",
                "message": "无法连接到打印机"
            }

    async def print_document(self, content: str, printer_name: str = "default") -> str:
        """打印文档"""
        logger.info("printer_handlers", f"打印文档到打印机: {printer_name}")

        if not content.strip():
            error_msg = "文档内容不能为空"
            logger.error("printer_handlers", error_msg)
            return error_msg

        try:
            # 准备打印请求数据
            print_data = {
                "content": content,
                "printer": printer_name,
                "options": {
                    "format": "text",
                    "encoding": "utf-8"
                }
            }

            # 调用打印API
            print_endpoint = self.settings.printer.endpoints.print_document
            result_data = await self.client.post(print_endpoint, print_data)

            # 构建成功消息
            document_size = len(content)
            base_message = f"文档已成功发送到打印机 '{printer_name}'"
            size_info = f"文档大小: {document_size} 字符"
            job_id = result_data.get("job_id", "unknown")
            job_info = f"打印任务ID: {job_id}"

            result = f"{base_message}\n{size_info}\n{job_info}"

            logger.info("printer_handlers", f"打印任务提交成功: {result}")
            return result

        except Exception as e:
            error_msg = f"打印失败: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return error_msg

    async def get_print_queue(self) -> dict:
        """获取打印队列状态"""
        logger.info("printer_handlers", "获取打印队列状态")

        try:
            queue_endpoint = self.settings.printer.endpoints.print_queue
            queue_data = await self.client.get(queue_endpoint)
            logger.info("printer_handlers", f"打印队列状态: {queue_data}")
            return queue_data

        except Exception as e:
            error_msg = f"获取打印队列失败: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return {
                "error": error_msg,
                "queue": [],
                "total_jobs": 0
            }

    async def get_printer_progress_sse(self, job_id: str) -> dict:
        """通过SSE获取打印进度（获取包含state字段的数据）"""
        logger.info("printer_handlers", f"获取打印进度: {job_id}")

        try:
            progress_data = await self.client.get_sse_with_field(
                self.settings.printer.endpoints.print_progress,
                "progress",  # 或者可能是 "state"，取决于实际数据结构
                params={"job_id": job_id}
            )
            logger.info("printer_handlers", f"打印进度: {progress_data}")
            return progress_data

        except Exception as e:
            error_msg = f"获取打印进度失败: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return {
                "error": error_msg,
                "job_id": job_id,
                "progress": 0,
                "status": "unknown"
            }

    async def set_nozzle_temperature(self, temperature: float) -> dict:
        """设置喷嘴温度"""
        logger.info("printer_handlers", f"设置喷嘴温度: {temperature}°C")

        try:
            # 验证温度范围（常见的3D打印机喷嘴温度范围）
            if temperature < 0 or temperature > 500:
                raise ValueError(f"温度值超出合理范围: {temperature}°C (应在0-500°C之间)")

            # 准备请求数据
            temperature_data = {
                "temperature": str(temperature)  # API要求字符串格式
            }

            # 调用设置喷嘴温度API
            temperature_endpoint = self.settings.printer.endpoints.temperature_nozzle
            result_data = await self.client.post(temperature_endpoint, temperature_data)

            logger.info("printer_handlers", f"喷嘴温度设置成功: {temperature}°C")
            # 检查API响应格式
            api_success = False
            api_message = "设置完成"

            if isinstance(result_data, dict):
                if result_data.get("code") == 200:
                    api_success = True
                    api_message = result_data.get("msg", "设置成功")
                elif result_data.get("success") is True:
                    api_success = True
                    api_message = result_data.get("message", "设置成功")

            return {
                "success": api_success,
                "temperature": temperature,
                "message": f"喷嘴温度已设置为 {temperature}°C - {api_message}",
                "api_response": result_data
            }

        except ValueError as e:
            error_msg = f"温度设置参数错误: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "temperature": temperature
            }
        except Exception as e:
            error_msg = f"设置喷嘴温度失败: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "temperature": temperature
            }

    async def set_bed_temperature(self, temperature: float) -> dict:
        """设置热床温度"""
        logger.info("printer_handlers", f"设置热床温度: {temperature}°C")

        try:
            # 验证温度范围（常见的3D打印机热床温度范围）
            if temperature < 0 or temperature > 150:
                raise ValueError(f"热床温度值超出合理范围: {temperature}°C (应在0-150°C之间)")

            # 准备请求数据
            temperature_data = {
                "temperature": str(temperature)  # API要求字符串格式
            }

            # 调用设置热床温度API
            temperature_endpoint = self.settings.printer.endpoints.temperature_bed
            result_data = await self.client.post(temperature_endpoint, temperature_data)

            logger.info("printer_handlers", f"热床温度设置成功: {temperature}°C")
            # 检查API响应格式
            api_success = False
            api_message = "设置完成"

            if isinstance(result_data, dict):
                if result_data.get("code") == 200:
                    api_success = True
                    api_message = result_data.get("msg", "设置成功")
                elif result_data.get("success") is True:
                    api_success = True
                    api_message = result_data.get("message", "设置成功")

            return {
                "success": api_success,
                "temperature": temperature,
                "message": f"热床温度已设置为 {temperature}°C - {api_message}",
                "api_response": result_data
            }

        except ValueError as e:
            error_msg = f"热床温度设置参数错误: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "temperature": temperature
            }
        except Exception as e:
            error_msg = f"设置热床温度失败: {str(e)}"
            logger.error("printer_handlers", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "temperature": temperature
            }


# 创建全局实例（同步封装）
_printer_handler_instance = None

def get_printer_handler() -> PrinterHandlers:
    """获取打印机处理器实例"""
    global _printer_handler_instance
    if _printer_handler_instance is None:
        _printer_handler_instance = PrinterHandlers()
    return _printer_handler_instance


# 同步封装函数（用于MCP工具调用）
def get_printer_status() -> dict:
    """获取打印机状态（同步版本）"""
    handler = get_printer_handler()
    return asyncio.run(handler.get_printer_status())


def print_document(content: str, printer_name: str = "default") -> str:
    """打印文档（同步版本）"""
    handler = get_printer_handler()
    return asyncio.run(handler.print_document(content, printer_name))


def get_print_queue() -> dict:
    """获取打印队列（同步版本）"""
    try:
        asyncio.get_running_loop()
        logger.warning("printer_handlers", "在事件循环中调用，返回模拟队列")
        return {"queue": [], "total_jobs": 0, "note": "需要异步架构支持"}
    except RuntimeError:
        handler = get_printer_handler()
        return asyncio.run(handler.get_print_queue())


def get_printer_progress(job_id: str) -> dict:
    """获取打印进度（同步版本）"""
    try:
        asyncio.get_running_loop()
        logger.warning("printer_handlers", "在事件循环中调用，返回模拟进度")
        return {
            "job_id": job_id,
            "progress": 50,
            "status": "模拟中",
            "note": "需要异步架构支持"
        }
    except RuntimeError:
        handler = get_printer_handler()
        return asyncio.run(handler.get_printer_progress_sse(job_id))


def set_nozzle_temperature(temperature: float) -> dict:
    """设置喷嘴温度（同步版本）"""
    try:
        # 检查是否在事件循环中运行
        loop = asyncio.get_running_loop()
        # 如果在事件循环中，创建任务来执行异步函数
        logger.info("printer_handlers", "在事件循环中调用，使用create_task执行")
        loop.create_task(get_printer_handler().set_nozzle_temperature(temperature))
        # 注意：这里我们不能直接等待，因为MCP工具需要同步返回
        # 但我们需要返回一个合理的响应而不是错误
        # 由于这是MCP工具调用的特殊情况，我们直接执行同步版本
        handler = get_printer_handler()
        return asyncio.run(handler.set_nozzle_temperature(temperature))
    except RuntimeError:
        # 不在事件循环中，正常使用asyncio.run
        handler = get_printer_handler()
        return asyncio.run(handler.set_nozzle_temperature(temperature))

