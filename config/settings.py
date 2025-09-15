"""
配置管理模块
支持环境变量、默认值和验证
"""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings  

from utils.logger import get_logger, log_config_load

# 初始化模块logger
logger = get_logger(__name__)


class LumiPilotSettings(BaseSettings):
    """
    Lumi Pilot 应用配置
    优先级：环境变量 > 默认值
    """
    
    # OpenAI 相关配置
    openai_api_key: str = Field(..., description="OpenAI API密钥")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API基础URL，支持兼容服务"
    )
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        description="默认使用的模型"
    )
    
    # 模型参数
    max_tokens: int = Field(default=1000, description="最大token数")
    temperature: float = Field(default=0.7, description="温度参数", ge=0.0, le=2.0)
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="lumi_pilot.log", description="日志文件名")
    enable_console_log: bool = Field(default=True, description="是否启用控制台日志")
    enable_file_log: bool = Field(default=True, description="是否启用文件日志")
    
    # 应用配置
    app_name: str = Field(default="Lumi Pilot", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是: {', '.join(valid_levels)}")
        return v.upper()
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_api_key(cls, v):
        """验证API密钥"""
        if not v or len(v.strip()) == 0:
            raise ValueError("OpenAI API密钥不能为空")
        return v.strip()
    
    class Config:
        env_prefix = "LUMI_"  # 环境变量前缀
        case_sensitive = False
        

# 全局配置实例
_settings: Optional[LumiPilotSettings] = None


def get_settings() -> LumiPilotSettings:
    """
    获取配置实例（单例模式）
    
    Returns:
        LumiPilotSettings: 配置实例
    """
    global _settings
    if _settings is None:
        try:
            _settings = LumiPilotSettings()
            logger.info("配置加载成功", event_type="config_init")
        except Exception as e:
            logger.error("配置加载失败", error=str(e), event_type="config_error")
            raise RuntimeError(f"配置加载失败: {e}")
    return _settings


def reload_settings() -> LumiPilotSettings:
    """
    重新加载配置
    
    Returns:
        LumiPilotSettings: 新的配置实例
    """
    global _settings
    _settings = None
    return get_settings()


def validate_environment() -> tuple[bool, list[str]]:
    """
    验证环境配置是否完整
    
    Returns:
        tuple[bool, list[str]]: (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查必需的环境变量
    required_vars = [
        "LUMI_OPENAI_API_KEY",
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"缺少必需的环境变量: {var}")
    
    # 尝试创建配置实例来触发验证
    try:
        get_settings()
    except Exception as e:
        errors.append(f"配置验证失败: {e}")
    
    return len(errors) == 0, errors


def print_current_config() -> None:
    """打印当前配置（不包含敏感信息）"""
    try:
        settings = get_settings()
        print("当前配置:")
        print(f"  应用名称: {settings.app_name}")
        print(f"  模型: {settings.openai_model}")
        print(f"  基础URL: {settings.openai_base_url}")
        print(f"  最大Tokens: {settings.max_tokens}")
        print(f"  温度: {settings.temperature}")
        print(f"  日志级别: {settings.log_level}")
        print(f"  调试模式: {settings.debug}")
        print(f"  API密钥: {'*' * (len(settings.openai_api_key) - 4) + settings.openai_api_key[-4:]}")
    except Exception as e:
        print(f"获取配置失败: {e}")