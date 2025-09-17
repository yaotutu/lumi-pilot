"""
应用层核心实现
包含服务注册表和统一的服务调用入口
"""
import time
from typing import Dict, Optional
from .protocols import AIService
from .models import ServiceRequest, ServiceResponse


class ServiceRegistry:
    """
    服务注册表
    负责服务的注册、发现和管理
    """
    
    def __init__(self):
        self._services: Dict[str, AIService] = {}
    
    def register(self, name: str, service: AIService) -> None:
        """
        注册服务
        
        Args:
            name: 服务名称
            service: 服务实例
        """
        self._services[name] = service
    
    def get(self, name: str) -> AIService:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            AIService: 服务实例
            
        Raises:
            KeyError: 当服务不存在时
        """
        if name not in self._services:
            raise KeyError(f"服务 '{name}' 未注册")
        return self._services[name]
    
    def list_services(self) -> list[str]:
        """
        获取所有已注册的服务名称
        
        Returns:
            list[str]: 服务名称列表
        """
        return list(self._services.keys())
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        检查所有服务的健康状态
        
        Returns:
            Dict[str, bool]: 服务名称到健康状态的映射
        """
        results = {}
        for name, service in self._services.items():
            try:
                health = await service.health_check()
                results[name] = health.healthy
            except Exception:
                results[name] = False
        return results


class Application:
    """
    应用核心类
    提供统一的服务执行入口和生命周期管理
    """
    
    def __init__(self, registry: ServiceRegistry):
        """
        初始化应用
        
        Args:
            registry: 服务注册表
        """
        self.registry = registry
    
    async def execute(self, service_name: str, request: ServiceRequest) -> ServiceResponse:
        """
        执行服务请求
        
        Args:
            service_name: 服务名称
            request: 服务请求
            
        Returns:
            ServiceResponse: 服务响应
        """
        start_time = time.time()
        
        try:
            # 获取服务实例
            service = self.registry.get(service_name)
            
            # 执行服务请求
            response = await service.process(request)
            
            # 计算执行时间
            duration = time.time() - start_time
            response.metadata.duration = duration
            
            return response
            
        except KeyError as e:
            # 服务不存在错误
            duration = time.time() - start_time
            return ServiceResponse.error_response(
                error=str(e),
                service_name=service_name,
                action=request.action,
                request_id=request.context.request_id if request.context else "unknown",
                duration=duration
            )
        except Exception as e:
            # 其他执行错误
            duration = time.time() - start_time
            return ServiceResponse.error_response(
                error=f"服务执行失败: {str(e)}",
                service_name=service_name,
                action=request.action,
                request_id=request.context.request_id if request.context else "unknown",
                duration=duration
            )
    
    async def health_check(self) -> Dict[str, any]:
        """
        应用整体健康检查
        
        Returns:
            Dict[str, any]: 健康检查结果
        """
        service_health = await self.registry.health_check_all()
        all_healthy = all(service_health.values())
        
        return {
            "application_healthy": all_healthy,
            "services": service_health,
            "registered_services": self.registry.list_services()
        }


class ApplicationBuilder:
    """
    应用构建器
    负责创建和配置完整的应用实例，包括MCP初始化
    """
    
    @staticmethod
    async def create() -> Application:
        """
        创建完整配置的应用实例
        
        Returns:
            Application: 配置好的应用实例
        """
        from infrastructure.config import get_settings
        from infrastructure.llm import LLMClient
        from infrastructure.logging import get_logger
        from infrastructure.mcp import MCPFactory
        from services.chat import ChatService
        from services.fault_detection import FaultDetectionService
        
        logger = get_logger(__name__)
        settings = get_settings()
        
        # 初始化MCP管理器
        logger.info("application", "正在初始化MCP管理器...")
        mcp_manager = await MCPFactory.create_with_default_config()
        
        # 创建基础设施（将MCP管理器传递给LLM客户端）
        llm_client = LLMClient(mcp_manager=mcp_manager)
        
        # 创建服务注册表
        registry = ServiceRegistry()
        
        # 注册服务
        registry.register("chat", ChatService(llm_client, mcp_manager=mcp_manager))
        registry.register("fault_detection", FaultDetectionService(llm_client))
        
        # 创建应用
        return Application(registry)