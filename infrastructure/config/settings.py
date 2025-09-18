"""
简化的配置管理模块
只从TOML配置文件读取配置，不支持环境变量
"""
import toml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LumiPilotSettings(BaseModel):
    """
    Lumi Pilot 应用配置
    直接从config.toml文件读取所有配置
    """
    
    # OpenAI/LLM 配置
    openai_api_key: str = Field(..., description="OpenAI API密钥")
    openai_base_url: str = Field(..., description="OpenAI API基础URL")
    openai_model: str = Field(..., description="使用的模型")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=1000, description="最大token数")
    
    # 系统配置
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    
    # 日志配置
    log_file: str = Field(default="lumi_pilot.log", description="日志文件名")
    enable_console_log: bool = Field(default=True, description="是否启用控制台日志")
    enable_file_log: bool = Field(default=True, description="是否启用文件日志")
    
    # 应用配置
    app_name: str = Field(default="Lumi Pilot", description="应用名称")
    
    # 会话管理配置
    session_timeout_minutes: int = Field(default=30, description="会话超时时间（分钟）")
    session_max_messages: int = Field(default=20, description="单次会话最大消息数")
    session_max_tokens: int = Field(default=8000, description="单次会话最大token数")
    
    # 打印机配置
    printer_base_url: str = Field(..., description="打印机API基础URL")
    printer_timeout: int = Field(default=10, description="打印机请求超时时间")
    printer_debug: bool = Field(default=True, description="打印机调试模式")
    printer_status_endpoint: str = Field(..., description="打印机状态端点")
    printer_print_endpoint: str = Field(..., description="打印文档端点")
    printer_queue_endpoint: str = Field(..., description="打印队列端点")
    printer_progress_endpoint: str = Field(..., description="打印进度端点")
    
    # gRPC配置
    grpc_host: str = Field(default="localhost", description="gRPC服务器主机")
    grpc_port: int = Field(default=50051, description="gRPC服务器端口")
    grpc_max_workers: int = Field(default=10, description="gRPC最大工作线程数")


def load_toml_config() -> Dict[str, Any]:
    """
    加载TOML配置文件并返回扁平化的配置字典
    """
    config_path = Path(__file__).parent.parent.parent / "config.toml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)
    
    # 扁平化配置
    flat_config = {}
    
    # LLM配置
    if 'llm' in config:
        llm = config['llm']
        flat_config.update({
            'openai_api_key': llm.get('api_key'),
            'openai_base_url': llm.get('base_url'),
            'openai_model': llm.get('model'),
            'temperature': llm.get('temperature', 0.7),
            'max_tokens': llm.get('max_tokens', 1000),
        })
    
    # 系统配置
    if 'system' in config:
        system = config['system']
        flat_config.update({
            'debug': system.get('debug', False),
            'log_level': system.get('log_level', 'INFO'),
            'session_timeout_minutes': system.get('session_timeout_minutes', 30),
            'session_max_messages': system.get('session_max_messages', 20),
            'session_max_tokens': system.get('session_max_tokens', 8000),
        })
    
    # 日志配置
    if 'logging' in config:
        logging = config['logging']
        flat_config.update({
            'log_file': logging.get('file_path', 'lumi_pilot.log'),
            'enable_console_log': logging.get('enable_console', True),
            'enable_file_log': logging.get('enable_file', True),
        })
    
    # 应用配置
    flat_config.update({
        'app_name': 'Lumi Pilot',
    })
    
    # 打印机配置
    if 'printer' in config:
        printer = config['printer']
        flat_config.update({
            'printer_base_url': printer.get('base_url'),
            'printer_timeout': printer.get('timeout', 10),
            'printer_debug': printer.get('debug', True),
        })
        
        # 打印机端点
        if 'endpoints' in printer:
            endpoints = printer['endpoints']
            flat_config.update({
                'printer_status_endpoint': endpoints.get('status'),
                'printer_print_endpoint': endpoints.get('print_document'),
                'printer_queue_endpoint': endpoints.get('print_queue'),
                'printer_progress_endpoint': endpoints.get('print_progress'),
            })
    
    # gRPC配置
    if 'grpc' in config:
        grpc = config['grpc']
        flat_config.update({
            'grpc_host': grpc.get('host', 'localhost'),
            'grpc_port': grpc.get('port', 50051),
            'grpc_max_workers': grpc.get('max_workers', 10),
        })
    
    return flat_config


# 全局配置实例
_settings: Optional[LumiPilotSettings] = None


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


# 向后兼容的函数
def validate_environment():
    """验证配置（向后兼容）"""
    try:
        settings = get_settings()
        print(f"✅ 配置验证成功")
        print(f"📡 LLM模型: {settings.openai_model}")
        print(f"🖨️  打印机: {settings.printer_base_url}")
        return True
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def print_current_config():
    """打印当前配置（向后兼容）"""
    try:
        settings = get_settings()
        print("📋 当前配置:")
        print(f"  LLM模型: {settings.openai_model}")
        print(f"  LLM Base URL: {settings.openai_base_url}")
        print(f"  打印机: {settings.printer_base_url}")
        print(f"  调试模式: {settings.debug}")
    except Exception as e:
        print(f"❌ 无法读取配置: {e}")