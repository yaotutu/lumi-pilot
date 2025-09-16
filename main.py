#!/usr/bin/env python3
"""
Lumi Pilot AI服务平台
默认启动gRPC服务器

运行方式：
- 直接启动gRPC服务器: python main.py 或 uv run main.py
- CLI管理: uv run lumi-pilot
"""

import asyncio

from interfaces.grpc.server import main as grpc_main

if __name__ == "__main__":
    asyncio.run(grpc_main())