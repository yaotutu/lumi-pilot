#!/usr/bin/env python3
"""
测试增强功能：可观测性、错误处理、工具参数等
"""
import grpc
import json
from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc

def test_tool_call_with_observability():
    """测试工具调用和可观测性功能"""
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            client = lumi_pilot_pb2_grpc.LumiPilotServiceStub(channel)
            
            print("🔧 测试工具调用和可观测性...")
            request = lumi_pilot_pb2.ChatRequest(
                message="请调用打印机状态工具查看当前状态"
            )
            
            response = client.Chat(request)
            
            if response.success:
                print("✅ 工具调用成功")
                print(f"📝 AI回复: {response.message}")
                
                # 检查新增的可观测性字段
                print(f"🆔 Request ID: {response.metadata.request_id}")
                print(f"⏱️  LLM延迟: {response.metadata.llm_latency:.2f}s")
                print(f"🛠️  工具延迟: {response.metadata.tool_latency:.2f}s")
                print(f"🔧 工具调用数: {response.metadata.tools_used}")
                
                if hasattr(response.metadata, 'tool_call_ids') and response.metadata.tool_call_ids:
                    print(f"🔗 工具调用IDs: {list(response.metadata.tool_call_ids)}")
                
                if hasattr(response.metadata, 'generation_params'):
                    params = response.metadata.generation_params
                    print(f"⚙️  生成参数: model={params.get('model', 'N/A')}, temp={params.get('temperature', 'N/A')}")
                
            else:
                print(f"❌ 工具调用失败: {response.error}")
                
    except Exception as e:
        print(f"❌ 连接失败: {e}")

def test_normal_chat():
    """测试普通对话的可观测性"""
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            client = lumi_pilot_pb2_grpc.LumiPilotServiceStub(channel)
            
            print("\n💬 测试普通对话...")
            request = lumi_pilot_pb2.ChatRequest(
                message="你好，简单介绍一下自己"
            )
            
            response = client.Chat(request)
            
            if response.success:
                print("✅ 对话成功")
                print(f"📝 AI回复: {response.message[:100]}...")
                print(f"🆔 Request ID: {response.metadata.request_id}")
                print(f"⏱️  延迟: {response.metadata.llm_latency:.2f}s")
                print(f"🛠️  工具调用: {response.metadata.tools_used}")
            else:
                print(f"❌ 对话失败: {response.error}")
                
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    test_tool_call_with_observability()
    test_normal_chat()