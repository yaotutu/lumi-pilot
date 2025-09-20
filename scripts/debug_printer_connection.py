#!/usr/bin/env python3
"""
打印机连接诊断脚本
排查网络连接问题
"""
import asyncio
import os
import sys
import time

import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.config.settings import get_settings


async def test_basic_connectivity():
    """测试基本网络连通性"""
    print("🔍 基本网络连通性测试")
    print("=" * 40)

    settings = get_settings()
    base_url = settings.printer_base_url
    status_endpoint = settings.printer_status_endpoint
    full_url = f"{base_url}{status_endpoint}"

    print(f"📡 目标URL: {full_url}")
    print(f"⏱️  超时设置: {settings.printer_timeout}秒")

    # 1. 测试主机连通性
    print("\n1. 测试主机连通性...")
    host = base_url.replace("http://", "").replace("https://", "").split(":")[0]
    port = base_url.split(":")[-1].split("/")[0] if ":" in base_url else "80"
    print(f"   主机: {host}")
    print(f"   端口: {port}")

    # 使用curl测试连通性
    import subprocess
    try:
        # 测试主机是否可达
        ping_result = subprocess.run(['ping', '-c', '3', host],
                                   capture_output=True, text=True, timeout=10)
        if ping_result.returncode == 0:
            print(f"   ✅ 主机 {host} 可达")
        else:
            print(f"   ❌ 主机 {host} 不可达")
            print(f"   错误: {ping_result.stderr}")
    except subprocess.TimeoutExpired:
        print("   ⚠️  ping超时")
    except Exception as e:
        print(f"   ❌ ping测试失败: {e}")


async def test_http_request_steps():
    """分步测试HTTP请求"""
    print("\n2. 分步测试HTTP请求...")

    settings = get_settings()
    base_url = settings.printer_base_url
    status_endpoint = settings.printer_status_endpoint
    full_url = f"{base_url}{status_endpoint}"

    # 测试不同的超时设置
    timeouts = [1, 3, 5, 10]

    for timeout in timeouts:
        print(f"\n   测试超时 {timeout}秒:")
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(full_url)
                duration = time.time() - start_time
                print(f"   ✅ 请求成功 (耗时: {duration:.2f}s)")
                print(f"   📊 状态码: {response.status_code}")
                print(f"   📄 响应长度: {len(response.text)}字符")
                if response.status_code == 200:
                    print("   🎉 接口正常返回数据")
                    break
                return

        except httpx.TimeoutException:
            duration = time.time() - start_time
            print(f"   ⏰ 请求超时 (耗时: {duration:.2f}s)")

        except httpx.ConnectError as e:
            duration = time.time() - start_time
            print(f"   🔌 连接错误 (耗时: {duration:.2f}s): {e}")

        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ 请求异常 (耗时: {duration:.2f}s): {e}")


async def test_alternative_endpoints():
    """测试其他可能的端点"""
    print("\n3. 测试其他可能的端点...")

    settings = get_settings()
    base_url = settings.printer_base_url

    # 可能的端点
    endpoints = [
        "/",
        "/status",
        "/api/status",
        "/api/v1/status",
        "/api/v1.0/status",
        "/health",
        "/ping"
    ]

    for endpoint in endpoints:
        full_url = f"{base_url}{endpoint}"
        print(f"   测试: {full_url}")

        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(full_url)
                print(f"   ✅ {response.status_code} - 响应长度: {len(response.text)}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and len(data) > 0:
                            print(f"   🎯 可能找到正确端点: {endpoint}")
                            print(f"   📊 响应数据: {data}")
                    except Exception:
                        print(f"   📄 HTML响应: {response.text[:100]}...")

        except httpx.TimeoutException:
            print("   ⏰ 超时")
        except httpx.ConnectError:
            print("   🔌 连接失败")
        except Exception as e:
            print(f"   ❌ 错误: {e}")


def test_curl_command():
    """测试curl命令"""
    print("\n4. 测试curl命令...")

    settings = get_settings()
    base_url = settings.printer_base_url
    status_endpoint = settings.printer_status_endpoint
    full_url = f"{base_url}{status_endpoint}"

    curl_cmd = f"curl -v --connect-timeout 5 --max-time 10 '{full_url}'"
    print(f"   命令: {curl_cmd}")

    try:
        import subprocess
        result = subprocess.run(curl_cmd, shell=True, capture_output=True,
                              text=True, timeout=15)

        print(f"   返回码: {result.returncode}")
        if result.stdout:
            print(f"   输出: {result.stdout[:200]}...")
        if result.stderr:
            print(f"   错误: {result.stderr[:200]}...")

    except Exception as e:
        print(f"   curl测试失败: {e}")


async def main():
    """主诊断函数"""
    print("🔬 打印机连接问题诊断")
    print("🎯 排查HTTP请求卡住的原因\n")

    await test_basic_connectivity()
    await test_http_request_steps()
    await test_alternative_endpoints()
    test_curl_command()

    print(f"\n{'='*50}")
    print("📋 诊断建议:")
    print("1. 检查打印机设备是否开机")
    print("2. 确认网络连接是否正常")
    print("3. 验证IP地址和端口是否正确")
    print("4. 检查防火墙设置")
    print("5. 尝试在浏览器中直接访问URL")

    settings = get_settings()
    full_url = f"{settings.printer_base_url}{settings.printer_status_endpoint}"
    print(f"\n🔗 浏览器测试URL: {full_url}")


if __name__ == "__main__":
    asyncio.run(main())
