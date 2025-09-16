"""
日志模块
提供简洁的日志接口: logger.info("tag", "消息")
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Any

import structlog


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "lumi_pilot.log",
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    配置structlog日志系统
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置structlog处理器
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if enable_console:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准库logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台handler
    if enable_console:
        console_handler = logging.StreamHandler()
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


class SimpleLogger:
    """简化的日志记录器，tag+消息格式"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name.replace('lumi_pilot.', '').replace('__main__', 'main')
        self._logger = structlog.get_logger(self.module_name)
    
    def info(self, tag: str, message: str):
        """记录信息日志"""
        self._logger.info(message, tag=tag)
    
    def error(self, tag: str, message: str):
        """记录错误日志"""
        self._logger.error(message, tag=tag)
    
    def warning(self, tag: str, message: str):
        """记录警告日志"""
        self._logger.warning(message, tag=tag)
    
    def debug(self, tag: str, message: str):
        """记录调试日志"""
        self._logger.debug(message, tag=tag)


def get_logger(name: str) -> SimpleLogger:
    """
    获取简化的日志记录器
    
    Args:
        name: 日志记录器名称，通常使用 __name__
        
    Returns:
        SimpleLogger实例
        
    使用示例：
        logger = get_logger(__name__)
        logger.info("tag", "消息内容")
    """
    return SimpleLogger(name)