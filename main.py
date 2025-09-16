#!/usr/bin/env python3
"""
Lumi Pilot 现代化AI服务平台主入口

基于全新架构，支持：
- AI对话服务
- AI故障检测服务
- 统一的CLI和gRPC接口

运行方式：
- CLI: uv run main.py 或 uv run lumi-pilot
- 直接运行: python main.py
"""

from interfaces.cli import cli

if __name__ == "__main__":
    cli()