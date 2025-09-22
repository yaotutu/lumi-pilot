"""
摄像头捕获客户端 - 简化版本
直接HTTP请求获取MJPEG流的单帧图片
"""
import io
from typing import Optional

import httpx
from PIL import Image

from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class CameraCaptureClient:
    """
    摄像头捕获客户端 - 简化版
    大多数网络摄像头都支持MJPEG流，直接HTTP请求即可
    """

    def __init__(self, timeout: Optional[int] = None):
        """
        初始化摄像头捕获客户端

        Args:
            timeout: 请求超时时间（秒），为None时使用配置文件中的值
        """
        if timeout is None:
            settings = get_settings()
            self.timeout = settings.printer_monitoring.capture_timeout
        else:
            self.timeout = timeout

    async def capture_from_stream(self, stream_url: str) -> Optional[bytes]:
        """
        从MJPEG视频流中截取一帧图片

        Args:
            stream_url: 视频流URL

        Returns:
            bytes: JPEG格式的图片数据，失败时返回None
        """
        try:
            logger.info("capture", f"开始从视频流截图: {stream_url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream('GET', stream_url) as response:
                    if response.status_code != 200:
                        logger.error("http_request", f"HTTP请求失败: {response.status_code}")
                        return None

                    buffer = b""
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        buffer = buffer + chunk

                        # 寻找JPEG帧的开始和结束标记
                        jpeg_start = buffer.find(b'\xff\xd8')
                        if jpeg_start >= 0:
                            jpeg_end = buffer.find(b'\xff\xd9', jpeg_start)
                            if jpeg_end >= 0:
                                # 提取完整的JPEG数据
                                jpeg_data = buffer[jpeg_start:jpeg_end + 2]
                                logger.info("capture", f"成功截取图片，大小: {len(jpeg_data)} bytes")
                                return jpeg_data

                        # 防止缓冲区过大
                        if len(buffer) > 1024 * 1024:  # 1MB
                            buffer = buffer[-512 * 1024:]

                    logger.error("capture", "未能从视频流中找到完整的JPEG帧")
                    return None

        except Exception as e:
            logger.error("exception", f"视频流截图异常: {str(e)}")
            return None

    async def capture_from_mjpeg_stream(self, stream_url: str) -> Optional[bytes]:
        """
        备用方法，与capture_from_stream相同
        """
        return await self.capture_from_stream(stream_url)

    def validate_image(self, image_data: bytes) -> bool:
        """
        验证图片数据是否有效

        Args:
            image_data: 图片数据

        Returns:
            bool: 是否为有效图片
        """
        try:
            with io.BytesIO(image_data) as img_buffer:
                img = Image.open(img_buffer)
                img.verify()
                return True
        except Exception as e:
            logger.warning("validation", f"图片验证失败: {str(e)}")
            return False
