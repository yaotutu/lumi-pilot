"""
gRPC 客户端封装

用于连接 Lumi Pilot gRPC 服务器并调用服务方法。
"""

import grpc
from typing import Optional
from .generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc


class LumiPilotGRPCClient:
    """Lumi Pilot gRPC 客户端"""

    def __init__(self, grpc_host: str = "localhost", grpc_port: int = 50051):
        """
        初始化 gRPC 客户端

        Args:
            grpc_host: gRPC 服务器主机地址
            grpc_port: gRPC 服务器端口
        """
        self.grpc_host = grpc_host
        self.grpc_port = grpc_port
        self.target = f"{grpc_host}:{grpc_port}"
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[lumi_pilot_pb2_grpc.LumiPilotServiceStub] = None

    def connect(self):
        """建立 gRPC 连接"""
        if self._channel is None:
            self._channel = grpc.insecure_channel(self.target)
            self._stub = lumi_pilot_pb2_grpc.LumiPilotServiceStub(self._channel)

    def close(self):
        """关闭 gRPC 连接"""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None

    def chat(self, message: str) -> lumi_pilot_pb2.ChatResponse:
        """
        调用 Chat 方法

        Args:
            message: 用户消息

        Returns:
            ChatResponse protobuf 消息

        Raises:
            grpc.RpcError: gRPC 调用失败
        """
        self.connect()
        request = lumi_pilot_pb2.ChatRequest(message=message)
        return self._stub.Chat(request)

    def monitor_printer(self, camera_url: Optional[str] = None) -> lumi_pilot_pb2.PrinterMonitorResponse:
        """
        调用 MonitorPrinter 方法

        Args:
            camera_url: 摄像头 URL（可选）

        Returns:
            PrinterMonitorResponse protobuf 消息

        Raises:
            grpc.RpcError: gRPC 调用失败
        """
        self.connect()
        request = lumi_pilot_pb2.PrinterMonitorRequest()
        if camera_url:
            request.camera_url = camera_url
        return self._stub.MonitorPrinter(request)

    def health_check(self) -> bool:
        """
        检查 gRPC 服务器健康状态

        Returns:
            True: 服务器可用
            False: 服务器不可用
        """
        try:
            self.connect()
            # 尝试调用一个简单的方法来检查连接
            request = lumi_pilot_pb2.ChatRequest(message="health_check")
            response = self._stub.Chat(request, timeout=2)
            return True
        except Exception:
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


# 全局客户端实例（用于 FastAPI 依赖注入）
_global_client: Optional[LumiPilotGRPCClient] = None


def get_grpc_client() -> LumiPilotGRPCClient:
    """获取全局 gRPC 客户端实例"""
    global _global_client
    if _global_client is None:
        _global_client = LumiPilotGRPCClient()
    return _global_client


def set_grpc_target(host: str, port: int):
    """设置 gRPC 目标地址"""
    global _global_client
    _global_client = LumiPilotGRPCClient(grpc_host=host, grpc_port=port)
