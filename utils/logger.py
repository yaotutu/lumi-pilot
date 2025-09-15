"""
日志系统模块
提供结构化日志记录功能，支持不同级别和输出格式

使用规范：
1. 每个模块应该在文件顶部初始化自己的logger：
   logger = get_logger(__name__)

2. 使用统一的日志格式和标签：
   logger.info("操作描述", key1=value1, key2=value2)
   logger.error("错误描述", error=str(e), context={"key": "value"})

3. 关键业务节点记录：
   - API调用开始和结束
   - 重要配置加载
   - 错误和异常
   - 性能关键点
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "lumi_pilot.log",
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    初始化日志系统配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件名
        enable_console: 是否输出到控制台
        enable_file: 是否输出到文件
    """
    # 确保logs目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置处理器列表
    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # 根据输出配置选择处理器
    if enable_console:
        # 启用颜色支持，让终端正确显示
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    if enable_file:
        processors.append(structlog.processors.JSONRenderer())
    
    # 配置structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 配置标准库logging - 只用于文件输出
    import logging
    import logging.handlers
    
    # 设置根日志级别
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 只添加文件handler，控制台输出由structlog处理
    if enable_file:
        log_path = log_dir / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)


def get_logger(name: str, **extra_context: Any) -> structlog.BoundLogger:
    """
    获取结构化日志记录器，带模块标识
    
    Args:
        name: 日志记录器名称，通常使用 __name__
        **extra_context: 额外的上下文信息
        
    Returns:
        配置好的结构化日志记录器，已绑定模块信息
        
    使用示例：
        logger = get_logger(__name__)
        logger.info("操作完成", user_id=123, action="login")
    """
    # 简化模块名显示
    module_name = name.replace('lumi_pilot.', '').replace('__main__', 'main')
    
    # 创建带模块标识的logger
    logger = structlog.get_logger(module_name)
    
    # 绑定额外的上下文信息
    if extra_context:
        logger = logger.bind(**extra_context)
    
    return logger


def get_module_logger(module_name: str, component: Optional[str] = None) -> structlog.BoundLogger:
    """
    为特定模块创建专用logger
    
    Args:
        module_name: 模块名称
        component: 组件名称（可选）
        
    Returns:
        绑定了模块和组件信息的logger
        
    使用示例：
        logger = get_module_logger("api_client", "openai")
        logger.info("API调用开始", endpoint="/chat/completions")
    """
    logger_name = f"{module_name}.{component}" if component else module_name
    return structlog.get_logger(logger_name)


def log_api_call(
    logger: structlog.BoundLogger,
    model: str,
    input_text: str,
    response: str,
    duration: float,
    token_count: int = 0,
    **kwargs: Any
) -> None:
    """
    记录API调用信息
    
    Args:
        logger: 日志记录器
        model: 使用的模型名称
        input_text: 输入文本（会截断敏感信息）
        response: 响应内容（会截断）
        duration: 调用耗时（秒）
        token_count: 消耗的token数量
        **kwargs: 其他额外信息
    """
    # 截断长文本以避免日志过大
    max_length = 500
    truncated_input = input_text[:max_length] + "..." if len(input_text) > max_length else input_text
    truncated_response = response[:max_length] + "..." if len(response) > max_length else response
    
    logger.info(
        "API调用记录",
        event_type="api_call",
        model=model,
        input_text=truncated_input,
        response=truncated_response,
        duration=duration,
        token_count=token_count,
        input_length=len(input_text),
        response_length=len(response),
        **kwargs
    )


def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    context: Dict[str, Any],
    event: str = "错误发生"
) -> None:
    """
    记录错误信息
    
    Args:
        logger: 日志记录器
        error: 异常对象
        context: 错误上下文信息
        event: 事件描述
    """
    logger.error(
        event,
        error=str(error),
        error_type=type(error).__name__,
        **context
    )


def log_performance(
    logger: structlog.BoundLogger,
    operation: str,
    duration: float,
    **context: Any
) -> None:
    """
    记录性能信息
    
    Args:
        logger: 日志记录器
        operation: 操作名称
        duration: 耗时（秒）
        **context: 其他上下文信息
    """
    logger.info(
        f"{operation}完成",
        event_type="performance",
        operation=operation,
        duration=duration,
        duration_ms=round(duration * 1000, 2),
        **context
    )


def log_config_load(
    logger: structlog.BoundLogger,
    config_name: str,
    config_data: Dict[str, Any],
    success: bool = True
) -> None:
    """
    记录配置加载信息
    
    Args:
        logger: 日志记录器
        config_name: 配置名称
        config_data: 配置数据（敏感信息会被遮蔽）
        success: 是否成功
    """
    # 遮蔽敏感信息
    safe_config = {}
    for key, value in config_data.items():
        if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password']):
            safe_config[key] = f"***{str(value)[-4:]}" if len(str(value)) > 4 else "***"
        else:
            safe_config[key] = value
    
    log_level = "info" if success else "error"
    getattr(logger, log_level)(
        f"配置{config_name}{'加载成功' if success else '加载失败'}",
        event_type="config_load",
        config_name=config_name,
        config=safe_config,
        success=success
    )