#!/usr/bin/env python3
"""
TOML配置快速测试脚本
只测试配置加载功能，不进行网络请求
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.config.settings import get_settings, load_toml_config


def main():
    """快速配置测试"""
    print("⚡ TOML配置快速测试")
    print("=" * 40)
    
    print("1. TOML配置解析:")
    toml_config = load_toml_config()
    print(f"✅ 加载{len(toml_config)}个配置项")
    
    print("\n2. 打印机配置:")
    settings = get_settings()
    print(f"📡 Base URL: {settings.printer_base_url}")
    print(f"⏱️  Timeout: {settings.printer_timeout}s")
    print(f"🔧 Debug: {settings.printer_debug}")
    print(f"📊 状态端点: {settings.printer_status_endpoint}")
    
    print(f"\n✅ 配置统一管理成功！")
    print(f"🎯 现在所有配置都通过config.toml统一管理")


if __name__ == "__main__":
    main()