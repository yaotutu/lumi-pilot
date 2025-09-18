#!/usr/bin/env python3
"""
测试response_format参数支持
"""
import asyncio
from infrastructure.llm.client import LLMClient
from infrastructure.mcp.client import MCPManager

async def test_response_format():
    """测试response_format参数"""
    
    # 初始化LLM客户端
    llm_client = LLMClient(debug=True)
    
    print("🧪 测试1: 普通文本响应")
    response1 = await llm_client.chat(
        message="简单介绍一下Python",
        max_tokens=100
    )
    print(f"✅ 响应: {response1.message[:100]}...")
    print(f"🔧 生成参数: {response1.metadata.get('generation_params', {})}")
    
    print("\n🧪 测试2: JSON格式响应")
    response2 = await llm_client.chat(
        message="用JSON格式返回Python的三个主要特性，格式为: {\"features\": [\"特性1\", \"特性2\", \"特性3\"]}",
        response_format={"type": "json_object"},
        max_tokens=200
    )
    print(f"✅ 响应: {response2.message}")
    print(f"🔧 生成参数: {response2.metadata.get('generation_params', {})}")
    
    print("\n🧪 测试3: 额外参数支持")
    response3 = await llm_client.chat(
        message="说一个关于编程的笑话",
        temperature=0.9,
        top_p=0.8,
        stop=["\n\n"],
        max_tokens=100
    )
    print(f"✅ 响应: {response3.message}")
    print(f"🔧 生成参数: {response3.metadata.get('generation_params', {})}")

if __name__ == "__main__":
    asyncio.run(test_response_format())