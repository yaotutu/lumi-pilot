"""
服务协议定义
定义所有服务必须实现的接口标准
"""
from typing import Protocol

from .models import HealthStatus, ServiceRequest, ServiceResponse


class AIService(Protocol):
    """AI服务的标准接口协议"""

    async def process(self, request: ServiceRequest) -> ServiceResponse:
        """
        处理服务请求的核心方法

        Args:
            request: 标准化的服务请求

        Returns:
            ServiceResponse: 标准化的服务响应
        """
        ...

    async def health_check(self) -> HealthStatus:
        """
        检查服务健康状态

        Returns:
            HealthStatus: 服务健康状态信息
        """
        ...

    def get_service_name(self) -> str:
        """
        获取服务名称

        Returns:
            str: 服务名称
        """
        ...

    def get_supported_actions(self) -> list[str]:
        """
        获取支持的操作列表

        Returns:
            list[str]: 支持的操作名称列表
        """
        ...
