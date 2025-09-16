#!/usr/bin/env python3
"""
Lumi Pilot Python gRPC客户端示例
展示如何调用AI对话服务
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc


def main():
    """演示Lumi Pilot gRPC客户端调用"""
    
    # 连接到服务器
    with grpc.insecure_channel('localhost:50051') as channel:
        # 创建客户端
        client = lumi_pilot_pb2_grpc.LumiPilotServiceStub(channel)
        
        print("=== Lumi Pilot AI对话服务测试 ===\n")
        
        # 示例1: 基本对话
        print("1. 基本对话:")
        request = lumi_pilot_pb2.ChatRequest(
            message="你好，请介绍一下你自己"
        )
        
        try:
            response = client.Chat(request)
            if response.success:
                print(f"✅ AI回复: {response.message}")
                print(f"📊 模型: {response.metadata.model}")
                print(f"⏱️  耗时: {response.metadata.duration:.2f}秒")
            else:
                print(f"❌ 错误: {response.error}")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return
        
        print("\n" + "="*50 + "\n")
        
        # 示例2: 编程问题
        print("2. 编程问题:")
        request = lumi_pilot_pb2.ChatRequest(
            message="用Python写一个快速排序算法"
        )
        
        try:
            response = client.Chat(request)
            if response.success:
                print(f"✅ AI回复: {response.message[:200]}...")
                print(f"📊 模型: {response.metadata.model}")
                print(f"⏱️  耗时: {response.metadata.duration:.2f}秒")
                print(f"🆔 请求ID: {response.metadata.request_id}")
            else:
                print(f"❌ 错误: {response.error}")
        except Exception as e:
            print(f"❌ 请求失败: {e}")


if __name__ == "__main__":
    main()