"""
日志系统模块
提供结构化日志记录功能，支持不同级别和输出格式
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict

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
    
    # 配置标准库logging
    import logging
    import logging.handlers
    
    # 设置根日志级别
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)
    
    # 添加文件handler
    if enable_file:
        log_path = log_dir / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    获取结构化日志记录器
    
    Args:
        name: 日志记录器名称，通常使用 __name__
        
    Returns:
        配置好的结构化日志记录器
    """
    return structlog.get_logger(name)


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