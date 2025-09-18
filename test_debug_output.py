#!/usr/bin/env python3
"""
专门测试调试输出格式
"""
import grpc
from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc

def test_debug_output():
    """专门测试工具调用的调试输出"""
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            client = lumi_pilot_pb2_grpc.LumiPilotServiceStub(channel)
            
            print("🔧 发送工具调用请求，查看调试输出...")
            request = lumi_pilot_pb2.ChatRequest(
                message="请调用打印机状态工具查看打印机状态"
            )
            
            response = client.Chat(request)
            
            if response.success:
                print("✅ 工具调用成功")
                print(f"📝 AI回复: {response.message}")
                print(f"🆔 Request ID: {response.metadata.request_id}")
            else:
                print(f"❌ 工具调用失败: {response.error}")
                
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    test_debug_output()