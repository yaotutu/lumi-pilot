"""
FastAPI HTTP 服务器

将 HTTP 请求转发到 Lumi Pilot gRPC 服务器。
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import grpc
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 将主项目目录添加到 Python 路径（用于导入 generated 模块）
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

from .models import (
    ChatRequest,
    ChatResponse,
    PrinterMonitorRequest,
    PrinterMonitorResponse,
    HealthCheckResponse,
    ResponseMetadata,
)
from .grpc_client import get_grpc_client, set_grpc_target


# 创建 FastAPI 应用
app = FastAPI(
    title="Lumi Pilot HTTP Gateway",
    description="临时 HTTP 网关，用于将 HTTP 请求转发到 Lumi Pilot gRPC 服务器",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置（允许前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """服务器启动时的初始化"""
    # 从环境变量读取 gRPC 目标地址
    grpc_host = os.getenv("GRPC_HOST", "localhost")
    grpc_port = int(os.getenv("GRPC_PORT", "50051"))
    set_grpc_target(grpc_host, grpc_port)
    print(f"[HTTP Gateway] 已配置 gRPC 目标: {grpc_host}:{grpc_port}")


@app.on_event("shutdown")
async def shutdown_event():
    """服务器关闭时的清理"""
    client = get_grpc_client()
    client.close()
    print("[HTTP Gateway] gRPC 连接已关闭")


# ==================== API 端点 ====================

@app.get("/", response_class=JSONResponse)
async def root():
    """根路径"""
    return {
        "service": "Lumi Pilot HTTP Gateway",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    健康检查端点

    检查 HTTP 网关和后端 gRPC 服务器的状态。
    """
    client = get_grpc_client()
    grpc_healthy = client.health_check()

    return HealthCheckResponse(
        status="healthy" if grpc_healthy else "unhealthy",
        http_gateway="running",
        grpc_backend="connected" if grpc_healthy else "disconnected",
        grpc_target=client.target,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI 对话端点

    将用户消息转发到 gRPC Chat 服务。

    Args:
        request: ChatRequest，包含用户消息

    Returns:
        ChatResponse，包含 AI 回复

    Raises:
        HTTPException: gRPC 调用失败
    """
    client = get_grpc_client()

    try:
        # 调用 gRPC Chat 方法
        grpc_response = client.chat(request.message)

        # 转换为 HTTP 响应
        metadata = None
        if grpc_response.metadata:
            metadata = ResponseMetadata(
                request_id=grpc_response.metadata.request_id,
                model=grpc_response.metadata.model,
                duration=grpc_response.metadata.duration,
                timestamp=grpc_response.metadata.timestamp,
            )

        return ChatResponse(
            success=grpc_response.success,
            message=grpc_response.message,
            error=grpc_response.error if grpc_response.error else None,
            metadata=metadata,
        )

    except grpc.RpcError as e:
        # gRPC 错误处理
        error_message = f"gRPC 调用失败: {e.code()} - {e.details()}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_message,
        )
    except Exception as e:
        # 其他异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内部错误: {str(e)}",
        )


@app.post("/api/monitor-printer", response_model=PrinterMonitorResponse)
async def monitor_printer(request: PrinterMonitorRequest):
    """
    3D 打印机监控端点

    将打印机监控请求转发到 gRPC MonitorPrinter 服务。

    Args:
        request: PrinterMonitorRequest，包含摄像头 URL（可选）

    Returns:
        PrinterMonitorResponse，包含监控分析结果

    Raises:
        HTTPException: gRPC 调用失败
    """
    client = get_grpc_client()

    try:
        # 调用 gRPC MonitorPrinter 方法
        grpc_response = client.monitor_printer(request.camera_url)

        # 转换为 HTTP 响应
        return PrinterMonitorResponse(
            success=grpc_response.success,
            has_issues=grpc_response.has_issues,
            issue=grpc_response.issue,
            suggestion=grpc_response.suggestion,
            confidence=grpc_response.confidence,
            summary=grpc_response.summary,
            timestamp=grpc_response.timestamp,
            error=grpc_response.error if grpc_response.error else None,
        )

    except grpc.RpcError as e:
        # gRPC 错误处理
        error_message = f"gRPC 调用失败: {e.code()} - {e.details()}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_message,
        )
    except Exception as e:
        # 其他异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内部错误: {str(e)}",
        )


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    import uvicorn

    # 从环境变量读取 HTTP 服务器配置
    http_host = os.getenv("HTTP_HOST", "0.0.0.0")
    http_port = int(os.getenv("HTTP_PORT", "8000"))

    print(f"\n{'='*60}")
    print(f"  Lumi Pilot HTTP Gateway")
    print(f"{'='*60}")
    print(f"  HTTP 服务器: http://{http_host}:{http_port}")
    print(f"  API 文档: http://{http_host}:{http_port}/docs")
    print(f"  健康检查: http://{http_host}:{http_port}/health")
    print(f"{'='*60}\n")

    # 启动 HTTP 服务器
    uvicorn.run(
        app,
        host=http_host,
        port=http_port,
        log_level="info",
    )
