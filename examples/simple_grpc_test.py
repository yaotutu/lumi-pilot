#!/usr/bin/env python3
"""
简单的gRPC连接测试
用于诊断gRPC连接问题
"""
import sys
from pathlib import Path

import grpc

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc


def test_grpc_connection(server_address="localhost:50051"):
    """
    测试gRPC连接
    """
    print(f"🔗 测试连接到gRPC服务器: {server_address}")

    try:
        # 创建连接通道
        channel = grpc.insecure_channel(server_address)
        print("✅ gRPC通道创建成功")

        # 检查连接状态
        try:
            grpc.channel_ready_future(channel).result(timeout=10)
            print("✅ gRPC连接就绪")
        except grpc.FutureTimeoutError:
            print("❌ 连接超时，服务器可能未运行")
            return False

        # 创建客户端
        client = lumi_pilot_pb2_grpc.LumiPilotServiceStub(channel)
        print("✅ gRPC客户端创建成功")

        # 测试Chat方法
        print("\n🧪 测试Chat方法...")
        chat_request = lumi_pilot_pb2.ChatRequest(message="测试消息")
        try:
            chat_response = client.Chat(chat_request, timeout=30)
            print(f"✅ Chat调用成功: {chat_response.message[:50]}...")
        except Exception as e:
            print(f"❌ Chat调用失败: {e}")

        # 测试MonitorPrinter方法
        print("\n🧪 测试MonitorPrinter方法...")
        monitor_request = lumi_pilot_pb2.PrinterMonitorRequest()
        try:
            monitor_response = client.MonitorPrinter(monitor_request, timeout=60)
            print(f"✅ MonitorPrinter调用成功: 状态={monitor_response.status}")
        except Exception as e:
            print(f"❌ MonitorPrinter调用失败: {e}")

        # 关闭连接
        channel.close()
        print("\n✅ 所有测试完成")
        return True

    except Exception as e:
        print(f"❌ gRPC连接失败: {e}")
        return False


def main():
    """主函数"""
    print("🎯 gRPC连接诊断工具")
    print("=" * 40)

    # 测试不同的服务器地址
    addresses = [
        "localhost:50051",
        "127.0.0.1:50051",
        "0.0.0.0:50051"
    ]

    success = False
    for addr in addresses:
        print(f"\n📍 测试地址: {addr}")
        if test_grpc_connection(addr):
            success = True
            break
        print(f"❌ {addr} 连接失败")

    if not success:
        print("\n❌ 所有地址都连接失败")
        print("💡 请检查：")
        print("   1. 服务器是否正在运行 (python main.py)")
        print("   2. 端口50051是否被占用")
        print("   3. 防火墙设置")
        print("   4. gRPC依赖是否正确安装")


if __name__ == "__main__":
    main()
