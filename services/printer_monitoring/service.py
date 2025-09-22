"""
3D打印机监控服务实现 - 优化版
提供3D打印机状态监控、质量检测和异常识别功能，支持配置文件和调试模式
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.models import HealthStatus, ServiceRequest, ServiceResponse
from infrastructure.camera.capture import CameraCaptureClient
from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger
from infrastructure.vision.analyzer import VisionAnalysisClient

from .models import PrinterStatusRequest, PrinterStatusResponse

logger = get_logger(__name__)


class PrinterMonitoringService:
    """
    3D打印机监控服务类
    提供基于AI视觉分析的3D打印机状态监控功能
    支持配置文件管理和调试模式
    """

    def __init__(
        self, 
        camera_client: CameraCaptureClient = None,
        vision_client: VisionAnalysisClient = None
    ):
        """
        初始化3D打印机监控服务

        Args:
            camera_client: 摄像头捕获客户端实例
            vision_client: 视觉分析客户端实例
        """
        # 加载配置
        self.settings = get_settings()
        self.config = self.settings.printer_monitoring

        # 初始化客户端
        self.camera_client = camera_client or CameraCaptureClient(timeout=self.config.capture_timeout)
        self.vision_client = vision_client or VisionAnalysisClient()
        self.service_name = "printer_monitoring"

        # 调试模式设置
        self.debug_mode = self.config.debug_mode
        self.debug_save_path = Path(self.config.debug_save_path)

        if self.debug_mode:
            # 创建调试目录
            self.debug_save_path.mkdir(parents=True, exist_ok=True)
            logger.info("debug", f"调试模式已启用，文件保存路径: {self.debug_save_path}")

    def _save_debug_files(self, image_data: bytes, analysis_result: Any) -> dict:
        """
        保存调试文件（截图和分析结果）

        Args:
            image_data: 图片数据
            analysis_result: 分析结果

        Returns:
            dict: 保存的文件信息
        """
        if not self.debug_mode:
            return {}

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存截图
            image_filename = f"capture_{timestamp}.jpg"
            image_path = self.debug_save_path / image_filename

            with open(image_path, 'wb') as f:
                f.write(image_data)

            # 保存分析结果
            result_filename = f"analysis_{timestamp}.json"
            result_path = self.debug_save_path / result_filename

            result_data = {
                "timestamp": timestamp,
                "success": analysis_result.success,
                "analysis": analysis_result.analysis,
                "error": analysis_result.error,
                "metadata": analysis_result.metadata,
                "image_size": len(image_data),
                "config": {
                    "camera_url": self.config.camera_url,
                    "analysis_model": self.config.analysis_model
                }
            }

            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            # 清理旧文件（保持最大文件数量限制）
            self._cleanup_debug_files()

            logger.info("debug", f"调试文件已保存: {image_filename}, {result_filename}")

            return {
                "image_file": str(image_path),
                "result_file": str(result_path),
                "timestamp": timestamp
            }

        except Exception as e:
            logger.error("debug", f"保存调试文件失败: {str(e)}")
            return {}

    def _cleanup_debug_files(self):
        """清理旧的调试文件，保持在最大数量限制内"""
        try:
            # 获取所有调试文件
            image_files = list(self.debug_save_path.glob("capture_*.jpg"))
            result_files = list(self.debug_save_path.glob("analysis_*.json"))

            # 按修改时间排序
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 删除超出限制的文件
            max_files = self.config.max_debug_files

            for file_list in [image_files, result_files]:
                if len(file_list) > max_files:
                    files_to_delete = file_list[max_files:]
                    for file_path in files_to_delete:
                        file_path.unlink()
                        logger.debug("cleanup", f"已删除旧调试文件: {file_path.name}")

        except Exception as e:
            logger.warning("cleanup", f"清理调试文件时出错: {str(e)}")

    async def check_printer_status_simple(self, camera_url: str = None) -> PrinterStatusResponse:
        """
        简化的3D打印机状态检测方法

        Args:
            camera_url: 摄像头URL，如果不提供则使用配置文件中的URL

        Returns:
            PrinterStatusResponse: 检测结果
        """
        try:
            # 使用配置文件中的URL，如果没有传入参数
            url = camera_url or self.config.camera_url

            logger.info("monitoring", f"开始检测3D打印机状态，摄像头: {url}")

            # 截取图片
            image_data = await self.camera_client.capture_from_stream(url)
            if not image_data:
                image_data = await self.camera_client.capture_from_mjpeg_stream(url)

            if not image_data:
                return PrinterStatusResponse(
                    success=False,
                    status="error",
                    error=f"无法从摄像头获取图片: {url}"
                )

            # 分析图片
            analysis_result = await self.vision_client.analyze_printer_image(image_data)

            if not analysis_result.success:
                return PrinterStatusResponse(
                    success=False,
                    status="error", 
                    error=f"图片分析失败: {analysis_result.error}"
                )

            # 保存调试文件
            debug_info = self._save_debug_files(image_data, analysis_result)

            # 构建响应
            response = PrinterStatusResponse(
                success=True,
                status="analyzing",  # 默认值，会被覆盖
                image_captured=True,
                analysis_model=self.config.analysis_model,
                metadata={
                    "camera_url": url, 
                    "image_size": len(image_data),
                    "debug_mode": self.debug_mode,
                    **debug_info
                }
            )

            # 解析结构化结果
            if hasattr(analysis_result, 'metadata') and 'structured_result' in analysis_result.metadata:
                structured = analysis_result.metadata['structured_result']
                response.status = structured.get("status", "unknown")
                response.quality_score = structured.get("quality_score", 0)
                response.issues = structured.get("issues", [])
                response.recommendations = structured.get("recommendations", [])
                response.safety_alerts = structured.get("safety_alerts", [])
                response.summary = structured.get("summary", "")
            else:
                response.status = "analyzed"
                response.summary = analysis_result.analysis

            logger.info("monitoring", f"检测完成，状态: {response.status}, 评分: {response.quality_score}")
            return response

        except Exception as e:
            error_msg = f"检测过程异常: {str(e)}"
            logger.error("monitoring", error_msg)
            return PrinterStatusResponse(
                success=False,
                status="error",
                error=error_msg
            )

    async def process(self, request: ServiceRequest) -> ServiceResponse:
        """
        处理3D打印机监控请求

        Args:
            request: 标准化服务请求

        Returns:
            ServiceResponse: 标准化服务响应
        """
        action = request.action
        request_id = request.context.request_id if request.context else "unknown"

        try:
            if action == "check_printer_status":
                return await self._check_printer_status(request, request_id)
            elif action == "capture_and_analyze":
                return await self._check_printer_status(request, request_id)
            else:
                return ServiceResponse.error_response(
                    error=f"不支持的操作: {action}",
                    service_name=self.service_name,
                    action=action,
                    request_id=request_id
                )
        except Exception as e:
            return ServiceResponse.error_response(
                error=f"3D打印机监控处理失败: {str(e)}",
                service_name=self.service_name,
                action=action,
                request_id=request_id
            )

    async def _check_printer_status(self, request: ServiceRequest, request_id: str) -> ServiceResponse:
        """处理3D打印机状态检测请求"""
        # 解析请求参数
        if request.payload:
            printer_req = PrinterStatusRequest(**request.payload)
        else:
            printer_req = PrinterStatusRequest()

        # 调用简化版检测方法
        result = await self.check_printer_status_simple(printer_req.camera_url)

        if result.success:
            return ServiceResponse.success_response(
                data=result.model_dump(),
                service_name=self.service_name,
                action="check_printer_status",
                request_id=request_id
            )
        else:
            return ServiceResponse.error_response(
                error=result.error,
                service_name=self.service_name,
                action="check_printer_status",
                request_id=request_id
            )

    async def health_check(self) -> HealthStatus:
        """检查3D打印机监控服务健康状态"""
        try:
            vision_healthy = self.vision_client.validate_connection()

            return HealthStatus(
                healthy=vision_healthy,
                service_name=self.service_name,
                details={
                    "vision_client_healthy": vision_healthy,
                    "camera_url": self.config.camera_url,
                    "debug_mode": self.debug_mode,
                    "analysis_model": self.config.analysis_model,
                    "supported_actions": self.get_supported_actions()
                }
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                service_name=self.service_name,
                error=f"健康检查失败: {str(e)}"
            )

    def get_service_name(self) -> str:
        """获取服务名称"""
        return self.service_name

    def get_supported_actions(self) -> list[str]:
        """获取支持的操作列表"""
        return ["check_printer_status", "capture_and_analyze"]
