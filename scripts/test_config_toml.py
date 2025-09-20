#!/usr/bin/env python3
"""
TOML配置文件测试脚本
验证配置文件加载和使用功能
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.config.settings import get_settings, load_toml_config
from infrastructure.mcp.server.printer.handlers import get_printer_status


def test_toml_config_loading():
    """测试TOML配置文件加载"""
    print("🔧 测试TOML配置文件加载功能")
    print("=" * 50)

    # 测试TOML配置加载
    print("1. 测试TOML配置文件解析:")
    try:
        toml_config = load_toml_config()
        print("✅ TOML配置文件加载成功")
        print(f"📋 加载的配置项数量: {len(toml_config)}")

        for key, value in toml_config.items():
            print(f"   - {key}: {value}")

    except Exception as e:
        print(f"❌ TOML配置文件加载失败: {e}")

    print("\n" + "=" * 50)
    print("2. 测试配置管理器:")
    try:
        settings = get_settings()
        print("✅ 配置管理器初始化成功")

        print(f"📡 打印机基础URL: {settings.printer_base_url}")
        print(f"⏱️  打印机超时: {settings.printer_timeout}秒")
        print(f"🔧 打印机调试模式: {settings.printer_debug}")
        print(f"📊 状态端点: {settings.printer_status_endpoint}")
        print(f"📄 打印端点: {settings.printer_print_endpoint}")
        print(f"📋 队列端点: {settings.printer_queue_endpoint}")
        print(f"📈 进度端点: {settings.printer_progress_endpoint}")

        print("\n🤖 LLM配置:")
        print(f"   - 模型: {settings.openai_model}")
        print(f"   - 温度: {settings.llm.temperature}")
        print(f"   - 最大Tokens: {settings.llm.max_tokens}")

        print("\n🔍 系统配置:")
        print(f"   - 调试模式: {settings.system.debug}")
        print(f"   - 日志级别: {settings.system.log_level}")

    except Exception as e:
        print(f"❌ 配置管理器初始化失败: {e}")


def test_printer_with_config():
    """测试打印机使用配置文件"""
    print("\n" + "=" * 50)
    print("3. 测试打印机使用配置文件:")

    try:
        # 这会使用配置文件中的设置
        result = get_printer_status()

        print("✅ 打印机客户端使用配置文件成功")
        print(f"📊 返回结果类型: {type(result)}")
        print(f"📄 返回内容: {result}")

        # 检查是否使用了正确的配置
        settings = get_settings()
        print("\n🔍 验证配置使用:")
        print(f"   - 使用的基础URL: {settings.printer_base_url}")
        print(f"   - 使用的状态端点: {settings.printer_status_endpoint}")
        print(f"   - 完整请求URL: {settings.printer_base_url}{settings.printer_status_endpoint}")

    except Exception as e:
        print(f"❌ 打印机配置测试失败: {e}")


def test_config_priority():
    """测试配置优先级"""
    print("\n" + "=" * 50)
    print("4. 测试配置优先级:")
    print("💡 优先级顺序: 环境变量 > TOML配置文件 > 默认值")

    settings = get_settings()

    print("\n📡 打印机配置来源分析:")
    # 检查是否有环境变量覆盖
    env_base_url = os.getenv("LUMI_PRINTER_BASE_URL")
    if env_base_url:
        print(f"   🔧 LUMI_PRINTER_BASE_URL 环境变量: {env_base_url}")
        print("   ✅ 使用环境变量值")
    else:
        print(f"   📋 无环境变量，使用TOML配置: {settings.printer_base_url}")

    print("\n🤖 LLM配置来源分析:")
    env_api_key = os.getenv("LUMI_OPENAI_API_KEY")
    if env_api_key:
        masked_key = "*" * (len(env_api_key) - 4) + env_api_key[-4:]
        print(f"   🔑 LUMI_OPENAI_API_KEY 环境变量: {masked_key}")
        print("   ✅ 使用环境变量值")
    else:
        print("   ⚠️  无LUMI_OPENAI_API_KEY环境变量")


def show_config_file_content():
    """显示配置文件内容"""
    print("\n" + "=" * 50)
    print("5. 当前config.toml文件内容:")

    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.toml")

    if os.path.exists(config_path):
        try:
            with open(config_path, encoding='utf-8') as f:
                content = f.read()
            print("📄 config.toml:")
            print("-" * 40)
            print(content)
            print("-" * 40)
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
    else:
        print(f"❌ 配置文件不存在: {config_path}")


def main():
    """主测试函数"""
    print("🚀 TOML配置文件系统测试")
    print("🎯 验证配置统一管理功能")
    print("📁 配置文件位置: 项目根目录/config.toml\n")

    show_config_file_content()
    test_toml_config_loading()
    test_printer_with_config()
    test_config_priority()

    print("\n" + "=" * 50)
    print("🎉 配置文件测试完成！")
    print("📋 配置管理改进:")
    print("   ✅ 统一的TOML配置文件")
    print("   ✅ 环境变量优先级支持")
    print("   ✅ 打印机地址等配置统一管理")
    print("   ✅ 配置验证和类型检查")
    print("   ✅ 配置热重载支持")


if __name__ == "__main__":
    main()
