"""
打印机API客户端
封装HTTP请求，支持GET、POST和SSE请求
"""
from typing import Any

import httpx

from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class PrinterAPIClient:
    """打印机API客户端"""

    def __init__(self, base_url: str | None = None, timeout: int | None = None, debug: bool | None = None):
        """
        初始化打印机API客户端

        Args:
            base_url: 打印机API基础URL（如果为None，从配置文件读取）
            timeout: 请求超时时间（秒，如果为None，从配置文件读取）
            debug: 是否打印原始数据（如果为None，从配置文件读取）
        """
        # 从配置文件读取默认值
        settings = get_settings()

        self.base_url = (base_url or settings.printer.base_url).rstrip('/')
        self.timeout = timeout or settings.printer.timeout
        self.debug = debug if debug is not None else settings.printer.debug
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Lumi-Pilot-MCP/1.0"
        }
        logger.info("printer_client", f"初始化打印机客户端: {self.base_url}")
        if self.debug:
            print("\n🔧 [DEBUG] 初始化打印机客户端")
            print(f"📡 [DEBUG] Base URL: {self.base_url}")
            print(f"⏱️  [DEBUG] 超时时间: {self.timeout}秒")
            print(f"📋 [DEBUG] 请求头: {self.headers}")

    def _debug_print(self, title: str, data: any):
        """打印调试信息"""
        if self.debug:
            print(f"\n{'='*50}")
            print(f"🔍 [DEBUG] {title}")
            print(f"{'='*50}")
            print(f"{data}")
            print(f"{'='*50}")

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        发送GET请求

        Args:
            endpoint: API端点（例如: "/api/v1.0/home/print/status"）
            params: 查询参数

        Returns:
            API响应数据
        """
        url = f"{self.base_url}{endpoint}"
        logger.info("printer_client", f"发送GET请求: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()

                data = response.json()
                logger.info("printer_client", f"GET请求成功: {url}")
                return data

        except httpx.TimeoutException:
            error_msg = f"请求超时: {url}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {url}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"请求失败: {url}, 错误: {str(e)}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        发送POST请求

        Args:
            endpoint: API端点
            data: 请求数据

        Returns:
            API响应数据
        """
        url = f"{self.base_url}{endpoint}"
        logger.info("printer_client", f"发送POST请求: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=data,
                    headers=self.headers
                )
                response.raise_for_status()

                result = response.json()
                logger.info("printer_client", f"POST请求成功: {url}")
                return result

        except httpx.TimeoutException:
            error_msg = f"请求超时: {url}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {url}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"请求失败: {url}, 错误: {str(e)}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)

    async def get_sse_with_field(self, endpoint: str, required_field: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        发送SSE请求，获取第一个包含指定字段的完整消息数据

        Args:
            endpoint: API端点
            required_field: 必须包含的字段名（如 "state", "progress", "status" 等）
            params: 查询参数

        Returns:
            第一个包含指定字段的完整消息数据
        """
        url = f"{self.base_url}{endpoint}"
        logger.info("printer_client", f"发送SSE请求获取包含'{required_field}'字段的完整数据: {url}")

        try:
            sse_headers = {
                **self.headers,
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "GET",
                    url,
                    params=params,
                    headers=sse_headers
                ) as response:
                    response.raise_for_status()

                    # 读取SSE流，查找包含指定字段的消息
                    current_event = None
                    async for line in response.aiter_lines():
                        line = line.strip()

                        # 跳过空行
                        if not line:
                            continue

                        # 解析SSE事件类型 "event:msg"
                        if line.startswith("event:"):
                            current_event = line[6:]  # 去掉 "event:" 前缀
                            continue

                        # 解析SSE数据行 "data: {json}"
                        if line.startswith("data:"):
                            data_str = line[5:]  # 去掉 "data:" 前缀

                            # 跳过空数据或心跳
                            if not data_str or data_str == "[DONE]":
                                continue

                            try:
                                import json
                                data = json.loads(data_str)

                                # 检查是否包含指定字段
                                if required_field in data:
                                    logger.info("printer_client", f"SSE获取到包含'{required_field}'字段的完整消息 (事件类型: {current_event}): {data}")
                                    return data  # 返回整个消息数据
                                else:
                                    logger.debug("printer_client", f"SSE消息不包含'{required_field}'字段 (事件类型: {current_event}): {data}")

                            except json.JSONDecodeError:
                                logger.warning("printer_client", f"无法解析SSE数据: {data_str}")
                                continue

                    # 如果没有获取到包含指定字段的数据
                    raise Exception(f"未从SSE流中获取到包含'{required_field}'字段的数据")

        except httpx.TimeoutException:
            error_msg = f"SSE请求超时: {url}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"SSE HTTP错误 {e.response.status_code}: {url}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"SSE请求失败: {url}, 错误: {str(e)}"
            logger.error("printer_client", error_msg)
            raise Exception(error_msg)
