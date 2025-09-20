"""
配置管理模块 - 基于嵌套结构的最佳实践
使用Pydantic嵌套模型直接映射TOML配置
"""
from pathlib import Path
from typing import Any

import toml
from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    """系统配置"""
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    session_timeout_minutes: int = Field(default=30, description="会话超时时间（分钟）")
    session_max_messages: int = Field(default=20, description="单次会话最大消息数")
    session_max_tokens: int = Field(default=8000, description="单次会话最大token数")


class LLMConfig(BaseModel):
    """LLM配置"""
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(..., description="API基础URL")
    model: str = Field(..., description="使用的模型")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=1000, description="最大token数")
    timeout: int = Field(default=30, description="请求超时时间")


class PrinterEndpoints(BaseModel):
    """打印机API端点"""
    status: str = Field(..., description="状态端点")
    print_document: str = Field(..., description="打印文档端点")
    print_queue: str = Field(..., description="打印队列端点")
    print_progress: str = Field(..., description="打印进度端点")


class PrinterConfig(BaseModel):
    """打印机配置"""
    base_url: str = Field(..., description="打印机API基础URL")
    timeout: int = Field(default=10, description="请求超时时间")
    debug: bool = Field(default=True, description="调试模式")
    endpoints: PrinterEndpoints = Field(..., description="API端点")


class MCPConfig(BaseModel):
    """MCP配置"""
    enabled: bool = Field(default=True, description="是否启用MCP")
    timeout: int = Field(default=30, description="超时时间")


class GRPCConfig(BaseModel):
    """gRPC配置"""
    host: str = Field(default="localhost", description="服务器主机")
    port: int = Field(default=50051, description="服务器端口")
    max_workers: int = Field(default=10, description="最大工作线程数")


class LoggingConfig(BaseModel):
    """日志配置"""
    format: str = Field(default="structured", description="日志格式")
    file_path: str = Field(default="logs/lumi-pilot.log", description="日志文件路径")
    max_file_size: str = Field(default="10MB", description="最大文件大小")
    backup_count: int = Field(default=5, description="备份文件数量")
    enable_console: bool = Field(default=True, description="是否启用控制台日志")
    enable_file: bool = Field(default=True, description="是否启用文件日志")


class PersonalityConfig(BaseModel):
    """人物配置"""
    name: str = Field(default="Lumi", description="人物名称")
    description: str = Field(default="友善活泼的AI助手", description="人物描述")
    system_prompt: str = Field(..., description="系统提示词")
    humor_level: int = Field(default=7, description="幽默感 (0-10)")
    energy_level: int = Field(default=8, description="活泼程度 (0-10)")
    caring_level: int = Field(default=9, description="关心程度 (0-10)")
    formality: int = Field(default=3, description="正式程度 (0-10)")


class LumiPilotSettings(BaseModel):
    """
    Lumi Pilot 应用配置
    嵌套结构直接映射TOML配置
    """
    system: SystemConfig = Field(..., description="系统配置")
    llm: LLMConfig = Field(..., description="LLM配置")
    printer: PrinterConfig = Field(..., description="打印机配置")
    mcp: MCPConfig = Field(..., description="MCP配置")
    grpc: GRPCConfig = Field(..., description="gRPC配置")
    logging: LoggingConfig = Field(..., description="日志配置")
    personality: PersonalityConfig = Field(..., description="人物配置")


def load_toml_config() -> dict[str, Any]:
    """
    加载TOML配置文件并返回嵌套结构
    """
    config_path = Path(__file__).parent.parent.parent / "config.toml"

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, encoding='utf-8') as f:
        config = toml.load(f)

    # 处理人物配置中的名称变量替换
    if 'personality' in config and 'system_prompt' in config['personality']:
        name = config['personality'].get('name', 'Lumi')
        system_prompt = config['personality']['system_prompt']
        if '{name}' in system_prompt:
            config['personality']['system_prompt'] = system_prompt.format(name=name)

    return config


# 全局配置实例
_settings: LumiPilotSettings | None = None


def get_settings() -> LumiPilotSettings:
    """
    获取全局配置实例
    单例模式，首次调用时加载配置
    """
    global _settings
    if _settings is None:
        config_data = load_toml_config()
        _settings = LumiPilotSettings(**config_data)
    return _settings


def reload_settings():
    """
    重新加载配置（主要用于测试）
    """
    global _settings
    _settings = None
    return get_settings()


def validate_environment():
    """验证配置"""
    try:
        settings = get_settings()
        print("✅ 配置验证成功")
        print(f"📡 LLM模型: {settings.llm.model}")
        print(f"🖨️  打印机: {settings.printer.base_url}")
        return True
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def print_current_config():
    """打印当前配置"""
    try:
        settings = get_settings()
        print("📋 当前配置:")
        print(f"  LLM模型: {settings.llm.model}")
        print(f"  LLM Base URL: {settings.llm.base_url}")
        print(f"  打印机: {settings.printer.base_url}")
        print(f"  调试模式: {settings.system.debug}")
    except Exception as e:
        print(f"❌ 无法读取配置: {e}")
