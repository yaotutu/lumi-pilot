#!/usr/bin/env python3
"""
3D打印机监控 gRPC 客户端示例
演示如何调用 MonitorPrinter 接口进行一次完整的截图+分析流程
"""
import sys
from pathlib import Path

import grpc

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc


def monitor_printer(server_address="localhost:50051", camera_url=""):
    """
    调用3D打印机监控服务

    Args:
        server_address: gRPC服务器地址
        camera_url: 摄像头URL（可选，不提供则使用服务器配置的默认值）
    """
    print("🔗 连接到Lumi Pilot gRPC服务...")
    print(f"服务器地址: {server_address}")

    try:
        # 建立gRPC连接
        with grpc.insecure_channel(server_address) as channel:
            # 创建客户端存根
            client = lumi_pilot_pb2_grpc.LumiPilotServiceStub(channel)

            # 构建请求
            request = lumi_pilot_pb2.PrinterMonitorRequest()
            if camera_url:
                request.camera_url = camera_url
                print(f"📷 使用指定摄像头: {camera_url}")
            else:
                print("📷 使用服务器默认摄像头")

            print("\n🎯 开始3D打印机监控...")
            print("流程: 视频流截图 → GLM-4.5V分析 → 返回结果")
            print("-" * 50)

            # 调用MonitorPrinter接口（一次完整的截图+分析流程）
            response = client.MonitorPrinter(request)

            # 处理响应
            print("\n📊 监控结果:")
            print(f"✅ 成功状态: {response.success}")

            if response.success:
                print(f"🔍 打印机状态: {response.status}")
                print(f"📏 质量评分: {response.quality_score}/100")
                print(f"📸 图片截取: {'成功' if response.image_captured else '失败'}")
                print(f"🤖 分析模型: {response.analysis_model}")

                # 显示发现的问题
                if response.issues:
                    print("\n⚠️  发现的问题:")
                    for i, issue in enumerate(response.issues, 1):
                        print(f"   {i}. {issue}")

                # 显示改进建议
                if response.recommendations:
                    print("\n💡 改进建议:")
                    for i, rec in enumerate(response.recommendations, 1):
                        print(f"   {i}. {rec}")

                # 显示安全警告
                if response.safety_alerts:
                    print("\n🚨 安全警告:")
                    for i, alert in enumerate(response.safety_alerts, 1):
                        print(f"   {i}. {alert}")

                # 显示AI分析摘要
                if response.summary:
                    print("\n📝 AI分析摘要:")
                    print(f"   {response.summary}")

                # 显示技术详情
                print("\n🔍 技术详情:")
                metadata = response.metadata
                print(f"   请求ID: {metadata.request_id}")
                print(f"   处理时长: {metadata.duration:.2f}秒")
                print(f"   时间戳: {metadata.timestamp}")
                print(f"   摄像头URL: {metadata.camera_url}")
                print(f"   图片大小: {metadata.image_size} bytes ({metadata.image_size/1024:.1f} KB)")
                print(f"   调试模式: {'启用' if metadata.debug_mode else '禁用'}")

                if metadata.debug_mode:
                    print("\n🐛 调试文件:")
                    if metadata.debug_image_file:
                        print(f"   截图文件: {metadata.debug_image_file}")
                    if metadata.debug_result_file:
                        print(f"   分析文件: {metadata.debug_result_file}")

            else:
                print(f"❌ 监控失败: {response.error}")

        print("\n🎉 监控完成!")

    except grpc.RpcError as e:
        print(f"❌ gRPC调用失败: {e.code()}: {e.details()}")
        print("请确保Lumi Pilot服务器正在运行 (python main.py)")

    except Exception as e:
        print(f"❌ 客户端异常: {str(e)}")


def main():
    """主函数"""
    print("🎥 3D打印机监控 gRPC 客户端")
    print("=" * 50)

    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="3D打印机监控gRPC客户端")
    parser.add_argument(
        "--server", 
        default="localhost:50051",
        help="gRPC服务器地址 (默认: localhost:50051)"
    )
    parser.add_argument(
        "--camera", 
        default="",
        help="摄像头URL (可选，不提供则使用服务器默认值)"
    )

    args = parser.parse_args()

    # 调用监控
    monitor_printer(args.server, args.camera)


if __name__ == "__main__":
    main()
