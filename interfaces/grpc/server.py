"""
gRPC服务器实现
启动gRPC服务器并注册服务处理器
"""
import asyncio
import signal
import sys
from concurrent import futures

import grpc

from core.application import ApplicationBuilder
from generated import lumi_pilot_pb2_grpc
from infrastructure.config import get_settings
from infrastructure.logging import get_logger, setup_logging

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
        self.server: grpc.Server | None = None
        self.application = None

    async def create_application(self):
        """
        创建应用实例

        Returns:
            Application: 配置好的应用实例
        """
        # 使用ApplicationBuilder创建完整配置的应用
        return await ApplicationBuilder.create()

    async def start(self):
        """
        启动gRPC服务器
        """
        logger.info("grpc_server", f"正在启动gRPC服务器 {self.host}:{self.port}")

        try:
            # 创建应用实例
            self.application = await self.create_application()

            # 从配置获取max_workers设置
            settings = get_settings()
            max_workers = settings.grpc.max_workers
            logger.info("grpc_server", f"gRPC服务器工作线程数: {max_workers}")

            # 创建gRPC服务器，禁用端口复用（端口独占模式）
            options = [('grpc.so_reuseport', 0)]  # 禁用端口复用
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers), options=options)

            # 注册服务处理器
            service_handler = LumiPilotServiceHandler(self.application)
            lumi_pilot_pb2_grpc.add_LumiPilotServiceServicer_to_server(service_handler, self.server)

            # 添加监听端口
            listen_addr = f"{self.host}:{self.port}"
            actual_port = self.server.add_insecure_port(listen_addr)

            # 检查端口是否被成功分配
            if actual_port == 0:
                raise RuntimeError(f"端口 {self.port} 已被占用，启用端口独占模式后只能有一个服务实例运行")
            elif actual_port != self.port:
                logger.warning("grpc_server", f"请求端口 {self.port} 不可用，gRPC已自动分配端口 {actual_port}")
                self.port = actual_port
                listen_addr = f"{self.host}:{self.port}"

            # 启动服务器
            self.server.start()
            import os
            logger.info("grpc_server", f"gRPC服务器已启动，监听地址: {listen_addr} (PID: {os.getpid()})")

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
        log_level=settings.system.log_level,
        log_file=settings.logging.file_path,
        enable_console=settings.logging.enable_console,
        enable_file=settings.logging.enable_file,
    )

    logger.info("grpc_main", "启动Lumi Pilot gRPC服务")

    # 创建并启动服务器，使用配置文件中的设置
    server = GRPCServer(host=settings.grpc.host, port=settings.grpc.port)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
