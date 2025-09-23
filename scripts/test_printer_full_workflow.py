#!/usr/bin/env python3
"""
3D打印机监控全流程测试脚本
测试: 视频流截图 + GLM-4.5V模型分析 + 结果输出
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import ServiceRequest
from infrastructure.llm.client import LLMClient
from services.printer_monitoring.service import PrinterMonitoringService


async def test_full_workflow():
    """测试完整的3D打印机监控流程"""
    print("🚀 3D打印机监控全流程测试")
    print("=" * 60)

    # 创建服务实例
    llm_client = LLMClient()
    service = PrinterMonitoringService(llm_client)

    print(f"🔧 服务名称: {service.get_service_name()}")
    print(f"📋 支持操作: {service.get_supported_actions()}")
    print(f"📷 摄像头URL: {service.config.camera_url}")
    print(f"🐛 调试模式: {'✅ 启用' if service.debug_mode else '❌ 禁用'}")

    # 健康检查
    print("\n🩺 服务健康检查...")
    health = await service.health_check()
    print(f"服务状态: {'✅ 健康' if health.healthy else '❌ 异常'}")

    if not health.healthy:
        print(f"❌ 健康检查失败: {health.error}")
        print("🔧 检查详情:")
        for key, value in health.details.items():
            print(f"   {key}: {value}")
        return False

    print("✅ 服务健康检查通过")

    # 执行完整流程测试
    print("\n🎯 开始全流程测试: 截图 → AI分析 → 结果输出")
    print("-" * 60)

    try:
        # 创建服务请求
        service_request = ServiceRequest(
            action="check_printer_status",
            payload={}
        )

        # 调用服务处理方法
        service_response = await service.process(service_request)

        # 显示结果
        print("\n📊 检测结果:")
        print(f"✅ 成功状态: {service_response.success}")

        if service_response.success:
            data = service_response.data
            print(f"🔍 打印机状态: {data.get('status', 'unknown')}")
            print(f"📸 图片截取: {'✅ 成功' if data.get('image_captured', False) else '❌ 失败'}")
            print(f"🤖 分析模型: {data.get('analysis_model', '')}")
            print(f"📏 质量评分: {data.get('quality_score', 0)}/100")

            if data.get('issues'):
                print("⚠️  发现问题:")
                for issue in data.get('issues', []):
                    print(f"   • {issue}")

            if data.get('recommendations'):
                print("💡 改进建议:")
                for rec in data.get('recommendations', []):
                    print(f"   • {rec}")

            if data.get('safety_alerts'):
                print("🚨 安全警告:")
                for alert in data.get('safety_alerts', []):
                    print(f"   • {alert}")

            if data.get('summary'):
                print("\n📝 AI分析总结:")
                print(f"   {data.get('summary', '')}")

            # 显示元数据
            if data.get('metadata'):
                print("\n🔍 技术详情:")
                for key, value in data.get('metadata', {}).items():
                    if key == "camera_url":
                        print(f"   📷 摄像头URL: {value}")
                    elif key == "image_size":
                        print(f"   📏 图片大小: {value} bytes ({value/1024:.1f} KB)")
                    else:
                        print(f"   {key}: {value}")

            # 保存详细结果到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 确保debug目录存在
            import os
            os.makedirs("debug/printer_monitoring", exist_ok=True)
            result_file = f"debug/printer_monitoring/analysis_{timestamp}.json"

            # 构建可序列化的结果数据
            result_data = {
                "timestamp": timestamp,
                "success": service_response.success,
                "data": data
            }

            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            print(f"\n💾 详细结果已保存: {result_file}")

            return True

        else:
            print(f"❌ 检测失败: {service_response.error}")
            return False

    except Exception as e:
        print(f"❌ 全流程测试异常: {str(e)}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        return False


async def test_multiple_runs():
    """测试多次运行的稳定性"""
    print("\n🔄 多次运行稳定性测试")
    print("-" * 40)

    # 创建服务实例
    llm_client = LLMClient()
    service = PrinterMonitoringService(llm_client)
    success_count = 0
    total_runs = 3

    for i in range(total_runs):
        print(f"\n🎯 第 {i+1}/{total_runs} 次测试...")

        try:
            # 创建服务请求
            service_request = ServiceRequest(
                action="check_printer_status",
                payload={}
            )

            # 调用服务处理方法
            service_response = await service.process(service_request)

            if service_response.success:
                success_count += 1
                data = service_response.data
                print(f"✅ 第 {i+1} 次成功 - 状态: {data.get('status', 'unknown')}")
            else:
                print(f"❌ 第 {i+1} 次失败: {service_response.error}")

        except Exception as e:
            print(f"❌ 第 {i+1} 次异常: {str(e)}")

        # 间隔3秒
        if i < total_runs - 1:
            print("⏳ 等待3秒...")
            await asyncio.sleep(3)

    success_rate = (success_count / total_runs) * 100
    print(f"\n📈 稳定性测试结果: {success_count}/{total_runs} 成功 ({success_rate:.1f}%)")


def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("🎥 3D打印机监控全流程测试工具")
    print("="*60)
    print("1. 单次全流程测试 (截图+AI分析)")
    print("2. 多次运行稳定性测试")
    print("3. 完整测试 (单次+多次)")
    print("4. 退出")
    print("="*60)


async def main():
    """主函数"""
    print("🚀 3D打印机监控全流程测试脚本")
    print("功能: 视频流截图 → GLM-4.5V分析 → 结果输出")

    while True:
        show_menu()

        try:
            choice = input("请选择测试项目 (1-4): ").strip()

            if choice == '1':
                success = await test_full_workflow()
                if success:
                    print("\n🎉 全流程测试完成！")
                else:
                    print("\n😞 全流程测试失败")

            elif choice == '2':
                await test_multiple_runs()

            elif choice == '3':
                print("\n🎯 开始完整测试...")
                success = await test_full_workflow()
                if success:
                    await test_multiple_runs()
                else:
                    print("❌ 单次测试失败，跳过多次测试")

            elif choice == '4':
                print("👋 测试结束，再见！")
                break

            else:
                print("❌ 无效选择，请输入1-4")

        except KeyboardInterrupt:
            print("\n\n👋 用户中断，测试结束")
            break
        except Exception as e:
            print(f"\n❌ 测试异常: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 程序被中断")
    except Exception as e:
        print(f"\n\n❌ 程序异常: {str(e)}")
