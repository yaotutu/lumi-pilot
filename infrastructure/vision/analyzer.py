"""
视觉分析客户端
使用GLM-4.5V模型进行图片分析
"""
import base64
import json

from infrastructure.config.settings import get_settings
from infrastructure.llm.openai_client import OpenAIClient
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class VisionAnalysisResult:
    """视觉分析结果"""

    def __init__(self, success: bool, analysis: str = "", error: str = "", metadata: dict = None):
        self.success = success
        self.analysis = analysis
        self.error = error
        self.metadata = metadata or {}


class VisionAnalysisClient:
    """
    视觉分析客户端
    专门用于处理图片分析任务，使用GLM-4.5V模型
    """

    def __init__(self):
        """初始化视觉分析客户端"""
        self.settings = get_settings()
        # 初始化OpenAI客户端，使用配置中的参数
        self.client = OpenAIClient(
            api_key=self.settings.llm.api_key,
            base_url=self.settings.llm.base_url,
            model="zai-org/GLM-4.5V",  # 固定使用GLM-4.5V模型
            max_tokens=1000,
            temperature=0.1
        )
        # 固定使用GLM-4.5V模型
        self.model = "zai-org/GLM-4.5V"

        # 3D打印机专用分析提示词
        self.printer_analysis_prompt = """你是一个专业的3D打印专家和质量检测员。请仔细分析这张3D打印机的照片，检测打印状态和质量问题。

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

    async def analyze_printer_image(self, image_data: bytes) -> VisionAnalysisResult:
        """
        分析3D打印机图片

        Args:
            image_data: 图片数据（bytes格式）

        Returns:
            VisionAnalysisResult: 分析结果
        """
        try:
            logger.info("printer_analysis", f"开始分析3D打印机图片，图片大小: {len(image_data)} bytes")

            # 将图片转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # 构建包含图片的消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.printer_analysis_prompt
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

            # 调用GLM-4.5V模型
            response = await self.client.chat_completion(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.1  # 使用较低的温度确保分析结果稳定
            )

            if response:
                analysis_text = response.content.strip()
                logger.info("printer_analysis", "3D打印机图片分析完成")

                # 尝试解析JSON结果
                try:
                    # 检查回复是否包含JSON格式
                    if "{" in analysis_text and "}" in analysis_text:
                        start_idx = analysis_text.find("{")
                        end_idx = analysis_text.rfind("}") + 1
                        json_str = analysis_text[start_idx:end_idx]
                        parsed_result = json.loads(json_str)

                        return VisionAnalysisResult(
                            success=True,
                            analysis=json.dumps(parsed_result, ensure_ascii=False, indent=2),
                            metadata={
                                "model": self.model,
                                "image_size": len(image_data),
                                "structured_result": parsed_result
                            }
                        )
                except json.JSONDecodeError:
                    logger.warning("json_parse", "无法解析JSON格式的分析结果，返回原始文本")

                # 如果JSON解析失败，返回原始分析文本
                return VisionAnalysisResult(
                    success=True,
                    analysis=analysis_text,
                    metadata={
                        "model": self.model,
                        "image_size": len(image_data)
                    }
                )
            else:
                error_msg = "视觉分析API调用失败"
                logger.error("api_call", error_msg)
                return VisionAnalysisResult(
                    success=False,
                    error=error_msg
                )

        except Exception as e:
            error_msg = f"视觉分析异常: {str(e)}"
            logger.error("exception", error_msg)
            return VisionAnalysisResult(
                success=False,
                error=error_msg
            )

    async def analyze_generic_image(self, image_data: bytes, custom_prompt: str) -> VisionAnalysisResult:
        """
        通用图片分析方法

        Args:
            image_data: 图片数据
            custom_prompt: 自定义分析提示词

        Returns:
            VisionAnalysisResult: 分析结果
        """
        try:
            logger.info("generic_analysis", f"开始通用图片分析，图片大小: {len(image_data)} bytes")

            # 将图片转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # 构建包含图片的消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": custom_prompt
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

            # 调用GLM-4.5V模型
            response = await self.client.chat_completion(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )

            if response:
                analysis_text = response.content.strip()
                logger.info("generic_analysis", "通用图片分析完成")

                return VisionAnalysisResult(
                    success=True,
                    analysis=analysis_text,
                    metadata={
                        "model": self.model,
                        "image_size": len(image_data)
                    }
                )
            else:
                error_msg = "通用视觉分析API调用失败"
                logger.error("api_call", error_msg)
                return VisionAnalysisResult(
                    success=False,
                    error=error_msg
                )

        except Exception as e:
            error_msg = f"通用视觉分析异常: {str(e)}"
            logger.error("exception", error_msg)
            return VisionAnalysisResult(
                success=False,
                error=error_msg
            )

    def validate_connection(self) -> bool:
        """
        验证视觉分析连接

        Returns:
            bool: 连接是否正常
        """
        try:
            # 检查配置
            if not self.settings.llm.api_key:
                logger.error("config", "LLM API密钥未配置")
                return False

            logger.info("validation", "视觉分析客户端连接验证通过")
            return True

        except Exception as e:
            logger.error("validation", f"视觉分析连接验证失败: {str(e)}")
            return False
