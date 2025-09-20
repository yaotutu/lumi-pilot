"""
MCP服务器响应模型定义
"""
from dataclasses import dataclass


@dataclass
class ServerInfo:
    """服务器信息响应模型"""
    server_name: str
    version: str
    type: str
    status: str
    tools_count: int
    description: str | None = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "server_name": self.server_name,
            "version": self.version,
            "type": self.type,
            "status": self.status,
            "tools_count": self.tools_count,
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class GreetingResponse:
    """问候响应模型"""
    message: str
    timestamp: str | None = None
    source: str = "Lumi Pilot Internal Server"

    def to_string(self) -> str:
        """转换为字符串格式"""
        return self.message
