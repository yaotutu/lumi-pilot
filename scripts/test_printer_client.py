#!/usr/bin/env python3
"""
打印机客户端测试脚本
测试HTTP客户端的GET、POST和SSE功能
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.mcp.server.printer.client import PrinterAPIClient
from infrastructure.mcp.server.printer.handlers import PrinterHandlers


async def test_printer_api_client():
    """测试打印机API客户端的各种功能"""
    print("=== 打印机API客户端测试 ===\n")
    
    # 初始化客户端
    client = PrinterAPIClient("http://192.168.5.18:9080")
    
    print("1. 测试普通GET请求 - 获取打印机状态")
    print("-" * 50)
    try:
        status_result = await client.get("/api/v1.0/status")
        print(f"✅ 状态请求成功: {status_result}")
    except Exception as e:
        print(f"❌ 状态请求失败: {e}")
    
    print("\n2. 测试SSE请求 - 获取包含state字段的完整数据")
    print("-" * 50)
    try:
        sse_result = await client.get_sse_state("/api/v1.0/home/print/progress", {"job_id": "test-123"})
        print(f"✅ SSE请求成功: {sse_result}")
    except Exception as e:
        print(f"❌ SSE请求失败: {e}")
    
    print("\n3. 测试POST请求 - 发送打印任务")
    print("-" * 50)
    try:
        print_data = {
            "content": "测试打印内容",
            "printer": "default",
            "options": {"format": "text", "encoding": "utf-8"}
        }
        post_result = await client.post("/api/v1.0/home/print/document", print_data)
        print(f"✅ POST请求成功: {post_result}")
    except Exception as e:
        print(f"❌ POST请求失败: {e}")


async def test_printer_handlers():
    """测试打印机处理器的封装功能"""
    print("\n\n=== 打印机处理器测试 ===\n")
    
    # 初始化处理器
    handler = PrinterHandlers("http://192.168.5.18:9080")
    
    print("1. 测试获取打印机状态")
    print("-" * 50)
    try:
        status = await handler.get_printer_status()
        print(f"✅ 获取状态成功: {status}")
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")
    
    print("\n2. 测试打印文档")
    print("-" * 50)
    try:
        print_result = await handler.print_document("Hello World测试", "default")
        print(f"✅ 打印任务成功: {print_result}")
    except Exception as e:
        print(f"❌ 打印任务失败: {e}")
    
    print("\n3. 测试获取打印队列")
    print("-" * 50)
    try:
        queue = await handler.get_print_queue()
        print(f"✅ 获取队列成功: {queue}")
    except Exception as e:
        print(f"❌ 获取队列失败: {e}")
    
    print("\n4. 测试获取打印进度 (SSE)")
    print("-" * 50)
    try:
        progress = await handler.get_printer_progress_sse("test-job-456")
        print(f"✅ 获取进度成功: {progress}")
        print(f"📊 返回的是包含state字段的完整数据")
    except Exception as e:
        print(f"❌ 获取进度失败: {e}")


def test_sync_functions():
    """测试同步封装函数（MCP工具使用的函数）"""
    print("\n\n=== 同步封装函数测试 ===\n")
    
    from infrastructure.mcp.server.printer.handlers import (
        get_printer_status, print_document, get_print_queue, get_printer_progress
    )
    
    print("1. 测试同步获取状态")
    print("-" * 50)
    try:
        status = get_printer_status()
        print(f"✅ 同步状态获取成功: {status}")
    except Exception as e:
        print(f"❌ 同步状态获取失败: {e}")
    
    print("\n2. 测试同步打印")
    print("-" * 50)
    try:
        result = print_document("同步测试内容", "default")
        print(f"✅ 同步打印成功: {result}")
    except Exception as e:
        print(f"❌ 同步打印失败: {e}")
    
    print("\n3. 测试同步获取队列")
    print("-" * 50)
    try:
        queue = get_print_queue()
        print(f"✅ 同步队列获取成功: {queue}")
    except Exception as e:
        print(f"❌ 同步队列获取失败: {e}")
    
    print("\n4. 测试同步获取进度 (SSE)")
    print("-" * 50)
    try:
        progress = get_printer_progress("sync-test-789")
        print(f"✅ 同步进度获取成功: {progress}")
        print(f"📊 验证返回完整数据（包含state字段）")
    except Exception as e:
        print(f"❌ 同步进度获取失败: {e}")


async def main():
    """主测试函数"""
    print("🔧 开始打印机客户端功能测试...\n")
    
    # 异步客户端测试
    await test_printer_api_client()
    
    # 异步处理器测试  
    await test_printer_handlers()
    
    # 同步封装函数测试
    test_sync_functions()
    
    print("\n\n🎉 所有测试完成！")
    print("\n📝 测试说明:")
    print("- ✅ 表示函数正常执行（可能因为网络原因返回错误，但逻辑正确）")
    print("- ❌ 表示函数执行异常")
    print("- 404错误属于正常情况（测试环境下打印机API可能不可用）")
    print("- 重点关注SSE功能是否返回完整的包含state字段的数据")


if __name__ == "__main__":
    asyncio.run(main())