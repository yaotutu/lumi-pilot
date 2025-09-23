"""
3D打印机监控服务实现 - 优化版
提供3D打印机状态监控、质量检测和异常识别功能，支持配置文件和调试模式
"""
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.models import HealthStatus, ServiceRequest, ServiceResponse
from infrastructure.camera.capture import CameraCaptureClient
from infrastructure.config.settings import get_settings
from infrastructure.logging.logger import get_logger
from infrastructure.llm.client import LLMClient

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
        llm_client: LLMClient,
        camera_client: CameraCaptureClient = None
    ):
        """
        初始化3D打印机监控服务

        Args:
            llm_client: LLM客户端实例
            camera_client: 摄像头捕获客户端实例
        """
        # 加载配置
        self.settings = get_settings()
        self.config = self.settings.printer_monitoring

        # 初始化客户端
        self.llm_client = llm_client
        self.camera_client = camera_client or CameraCaptureClient(timeout=self.config.capture_timeout)
        self.service_name = "printer_monitoring"

        # 调试模式设置
        self.debug_mode = self.config.debug_mode
        self.debug_save_path = Path(self.config.debug_save_path)

        if self.debug_mode:
            # 创建调试目录
            self.debug_save_path.mkdir(parents=True, exist_ok=True)
            logger.info("debug", f"调试模式已启用，文件保存路径: {self.debug_save_path}")

    def _save_debug_files(self, image_data: bytes, analysis_result: str) -> dict:
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
                "analysis": analysis_result,
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

    def _load_analysis_prompt(self) -> str:
        """
        加载3D打印机分析提示词

        Returns:
            str: 分析提示词
        """
        try:
            # 构建提示词文件路径
            prompt_path = Path(__file__).parent / "prompts" / "analysis_prompt.txt"
            
            # 如果特定于打印机监控的提示词文件不存在，尝试通用路径
            if not prompt_path.exists():
                prompt_path = Path(__file__).parent.parent.parent / "prompts" / "printer_monitoring" / "analysis_prompt.txt"
            
            # 如果文件存在，加载外部提示词
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            
            # 回退到默认提示词
            logger.warning("prompt", f"提示词文件不存在，使用默认提示词: {prompt_path}")
            return self._get_default_analysis_prompt()
            
        except Exception as e:
            logger.error("prompt", f"加载提示词失败，使用默认提示词: {str(e)}")
            return self._get_default_analysis_prompt()

    def _get_default_analysis_prompt(self) -> str:
        """
        获取默认的3D打印机分析提示词

        Returns:
            str: 默认分析提示词
        """
        return """你是一个专业的3D打印专家和质量检测员。请仔细分析这张3D打印机的照片，检测打印状态和质量问题。

请从以下方面进行分析：

1. **打印状态检测**：
   - 打印机是否正在工作
   - 打印进度评估
   - 打印头位置是否正常

2. **打印质量检查**：
   - 层间粘接是否良好
   - 是否有翘边(warping)现象
   - 表面质量是否平整
   - 填充密度是否合适

3. **异常问题识别**：
   - 线材是否缠绕或断裂
   - 喷头是否堵塞
   - 热床是否平整
   - 是否有支撑失效
   - 是否有拉丝或溢料现象

4. **安全检查**：
   - 是否有过热现象
   - 电气连接是否正常
   - 机械结构是否稳定

请用中文回复，格式如下：
{
  "status": "working/idle/error",
  "quality_score": 0-100,
  "issues": ["发现的问题列表"],
  "recommendations": ["改进建议"],
  "safety_alerts": ["安全警告（如有）"],
  "summary": "整体评估总结"
}"""

    async def _analyze_printer_image(self, image_data: bytes) -> str:
        """
        使用LLM分析3D打印机图片

        Args:
            image_data: 图片数据（bytes格式）

        Returns:
            str: 分析结果
        """
        try:
            logger.info("printer_analysis", f"开始分析3D打印机图片，图片大小: {len(image_data)} bytes")

            # 将图片转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # 加载3D打印机专用分析提示词
            printer_analysis_prompt = self._load_analysis_prompt()

            # 构建包含图片的消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": printer_analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            # 通过LLMClient的_openai_client调用视觉分析
            response = await self.llm_client._client.chat_completion(
                messages=messages,
                model=self.config.analysis_model,
                max_tokens=1000,
                temperature=0.1  # 使用较低的温度确保分析结果稳定
            )

            if response:
                analysis_text = response.content.strip()
                logger.info("printer_analysis", "3D打印机图片分析完成")
                return analysis_text
            else:
                raise Exception("视觉分析API调用失败")

        except Exception as e:
            error_msg = f"视觉分析异常: {str(e)}"
            logger.error("exception", error_msg)
            raise Exception(error_msg)

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
        try:
            # 解析请求参数
            if request.payload:
                printer_req = PrinterStatusRequest(**request.payload)
            else:
                printer_req = PrinterStatusRequest()

            # 使用配置文件中的URL，如果没有传入参数
            url = printer_req.camera_url or self.config.camera_url

            logger.info("monitoring", f"开始检测3D打印机状态，摄像头: {url}")

            # 截取图片
            image_data = await self.camera_client.capture_from_stream(url)
            if not image_data:
                image_data = await self.camera_client.capture_from_mjpeg_stream(url)

            if not image_data:
                return ServiceResponse.error_response(
                    error=f"无法从摄像头获取图片: {url}",
                    service_name=self.service_name,
                    action="check_printer_status",
                    request_id=request_id
                )

            # 分析图片
            try:
                analysis_result = await self._analyze_printer_image(image_data)
            except Exception as e:
                return ServiceResponse.error_response(
                    error=f"图片分析失败: {str(e)}",
                    service_name=self.service_name,
                    action="check_printer_status",
                    request_id=request_id
                )

            # 保存调试文件
            debug_info = self._save_debug_files(image_data, analysis_result)

            # 解析分析结果
            response_data = {
                "success": True,
                "status": "analyzing",  # 默认值，会被覆盖
                "image_captured": True,
                "analysis_model": self.config.analysis_model,
                "metadata": {
                    "camera_url": url, 
                    "image_size": len(image_data),
                    "debug_mode": self.debug_mode,
                    **debug_info
                }
            }

            # 尝试解析JSON格式的分析结果
            try:
                import json
                # 检查回复是否包含JSON格式
                if "{" in analysis_result and "}" in analysis_result:
                    start_idx = analysis_result.find("{")
                    end_idx = analysis_result.rfind("}") + 1
                    json_str = analysis_result[start_idx:end_idx]
                    parsed_result = json.loads(json_str)
                    
                    response_data["status"] = parsed_result.get("status", "unknown")
                    response_data["quality_score"] = parsed_result.get("quality_score", 0)
                    response_data["issues"] = parsed_result.get("issues", [])
                    response_data["recommendations"] = parsed_result.get("recommendations", [])
                    response_data["safety_alerts"] = parsed_result.get("safety_alerts", [])
                    response_data["summary"] = parsed_result.get("summary", "")
                else:
                    response_data["status"] = "analyzed"
                    response_data["summary"] = analysis_result
            except json.JSONDecodeError:
                response_data["status"] = "analyzed"
                response_data["summary"] = analysis_result

            logger.info("monitoring", f"检测完成，状态: {response_data['status']}, 评分: {response_data.get('quality_score', 0)}")
            
            return ServiceResponse.success_response(
                data=response_data,
                service_name=self.service_name,
                action="check_printer_status",
                request_id=request_id
            )

        except Exception as e:
            error_msg = f"检测过程异常: {str(e)}"
            logger.error("monitoring", error_msg)
            return ServiceResponse.error_response(
                error=error_msg,
                service_name=self.service_name,
                action="check_printer_status",
                request_id=request_id
            )

    async def health_check(self) -> HealthStatus:
        """检查3D打印机监控服务健康状态"""
        try:
            # 检查LLM连接
            llm_healthy = await self.llm_client.validate_connection()

            return HealthStatus(
                healthy=llm_healthy,
                service_name=self.service_name,
                details={
                    "llm_client_healthy": llm_healthy,
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
