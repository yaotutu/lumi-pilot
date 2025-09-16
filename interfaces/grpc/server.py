"""
gRPC服务器实现
启动gRPC服务器并注册服务处理器
"""
import asyncio
import signal
import sys
from concurrent import futures
from typing import Optional

import grpc


from core.application import Application, ServiceRegistry
from infrastructure.config import get_settings
from infrastructure.llm import LLMClient
from infrastructure.logging import setup_logging, get_logger
from services.chat import ChatService
from services.fault_detection import FaultDetectionService
from generated import lumi_pilot_pb2_grpc
from .handlers import LumiPilotServiceHandler

# 初始化模块logger
logger = get_logger(__name__)


class GRPCServer:
    """
    gRPC服务器类
    负责启动和管理gRPC服务
    """
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        """
        初始化gRPC服务器
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
        """
        self.host = host
        self.port = port
        self.server: Optional[grpc.Server] = None
        self.application: Optional[Application] = None
    
    async def create_application(self) -> Application:
        """
        创建应用实例
        
        Returns:
            Application: 配置好的应用实例
        """
        # 获取配置
        settings = get_settings()
        
        # 创建基础设施
        llm_client = LLMClient()
        
        # 创建服务注册表
        registry = ServiceRegistry()
        
        # 注册服务
        registry.register("chat", ChatService(llm_client))
        registry.register("fault_detection", FaultDetectionService(llm_client))
        
        # 创建应用
        return Application(registry)
    
    async def start(self):
        """
        启动gRPC服务器
        """
        logger.info("grpc_server", f"正在启动gRPC服务器 {self.host}:{self.port}")
        
        try:
            # 创建应用实例
            self.application = await self.create_application()
            
            # 创建gRPC服务器
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # 注册服务处理器
            service_handler = LumiPilotServiceHandler(self.application)
            lumi_pilot_pb2_grpc.add_LumiPilotServiceServicer_to_server(service_handler, self.server)
            
            # 添加监听端口
            listen_addr = f"{self.host}:{self.port}"
            self.server.add_insecure_port(listen_addr)
            
            # 启动服务器
            self.server.start()
            logger.info("grpc_server", f"gRPC服务器已启动，监听地址: {listen_addr}")
            
            # 设置信号处理器
            self._setup_signal_handlers()
            
            # 等待服务器终止
            self.server.wait_for_termination()
            
        except KeyboardInterrupt:
            logger.info("grpc_server", "收到键盘中断信号，正在关闭服务器...")
            self.stop()
        except Exception as e:
            logger.error("grpc_server", f"gRPC服务器启动失败: {str(e)}")
            sys.exit(1)
    
    def stop(self):
        """
        停止gRPC服务器
        """
        if self.server:
            logger.info("grpc_server", "正在停止gRPC服务器...")
            self.server.stop(grace=5.0)  # 5秒优雅关闭
            logger.info("grpc_server", "gRPC服务器已停止")
    
    def _setup_signal_handlers(self):
        """
        设置信号处理器
        """
        def signal_handler(signum, frame):
            logger.info("grpc_server", f"收到信号 {signum}，正在关闭服务器...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """
    gRPC服务器主函数
    """
    # 初始化日志
    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        enable_console=settings.enable_console_log,
        enable_file=settings.enable_file_log,
    )
    
    logger.info("grpc_main", "启动Lumi Pilot gRPC服务")
    
    # 创建并启动服务器
    server = GRPCServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())