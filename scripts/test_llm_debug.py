#!/usr/bin/env python3
"""
LLM调试功能测试脚本
测试LLM客户端的原始数据打印功能
"""
import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.llm.client import LLMClient
from infrastructure.mcp.client.manager import MCPManager


async def test_llm_debug_output():
    """测试LLM调试输出功能"""
    print("🚀 LLM调试功能测试")
    print("🎯 将打印所有发送给LLM和从LLM接收的原始数据")
    print("=" * 60)
    
    # 初始化MCP管理器（包含打印机工具）
    print("📡 初始化MCP管理器...")
    mcp_manager = MCPManager()
    await mcp_manager.connect_all()
    
    # 初始化LLM客户端（启用调试模式）
    print("🔧 初始化LLM客户端（调试模式开启）...")
    llm_client = LLMClient(mcp_manager=mcp_manager, debug=True)
    
    print("\n" + "=" * 60)
    print("🧪 测试1: 简单对话（无工具调用）")
    print("=" * 60)
    
    response = await llm_client.chat(
        message="你好，请简单介绍一下你自己",
        system_prompt="你是一个AI助手",
        enable_tools=False
    )
    
    print(f"\n✅ 对话完成: {response.success}")
    print(f"📝 响应长度: {len(response.message)}字符")
    
    print("\n" + "=" * 60)
    print("🧪 测试2: 带工具调用的对话")
    print("=" * 60)
    
    response = await llm_client.chat(
        message="请帮我检查一下打印机的状态",
        system_prompt="你是一个智能助手，可以调用打印机工具来帮助用户",
        enable_tools=True
    )
    
    print(f"\n✅ 工具调用对话完成: {response.success}")
    print(f"📝 响应长度: {len(response.message)}字符")
    if response.metadata.get("tools_used", 0) > 0:
        print(f"🔧 使用了 {response.metadata['tools_used']} 个工具")
    
    # 清理
    await mcp_manager.disconnect_all()


async def test_simple_llm_call():
    """测试简单的LLM调用（不涉及MCP）"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 纯LLM调用（无MCP工具）")
    print("=" * 60)
    
    # 不使用MCP管理器的LLM客户端
    llm_client = LLMClient(mcp_manager=None, debug=True)
    
    response = await llm_client.chat(
        message="1+1等于多少？",
        system_prompt="你是一个数学助手",
        enable_tools=False
    )
    
    print(f"\n✅ 纯LLM调用完成: {response.success}")
    print(f"📝 响应: {response.message}")


def main():
    """主测试函数"""
    print("🔍 LLM调试数据输出测试")
    print("💡 此测试将显示所有LLM交互的原始数据")
    print("🎪 包括：发送的消息、工具定义、响应内容、工具调用等\n")
    
    # 运行异步测试
    asyncio.run(test_llm_debug_output())
    asyncio.run(test_simple_llm_call())
    
    print("\n" + "=" * 60)
    print("🎉 LLM调试功能测试完成！")
    print("📋 现在你可以看到所有LLM交互的详细原始数据")
    print("🔧 调试信息包括：")
    print("   - 发送给LLM的消息内容")
    print("   - 工具定义和参数")
    print("   - LLM响应的原始数据")
    print("   - MCP工具调用的请求和结果")
    print("   - 完整对话历史")


if __name__ == "__main__":
    main()