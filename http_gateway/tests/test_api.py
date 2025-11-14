"""
HTTP API 测试脚本

使用 httpx 测试 HTTP 网关的各个端点。

运行方式:
    uv run python tests/test_api.py
"""

import sys
import httpx


BASE_URL = "http://localhost:8000"


def test_root():
    """测试根路径"""
    print("\n[测试 1] 根路径 GET /")
    print("-" * 60)

    try:
        response = httpx.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_health():
    """测试健康检查"""
    print("\n[测试 2] 健康检查 GET /health")
    print("-" * 60)

    try:
        response = httpx.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"服务状态: {data.get('status')}")
        print(f"HTTP 网关: {data.get('http_gateway')}")
        print(f"gRPC 后端: {data.get('grpc_backend')}")
        print(f"gRPC 目标: {data.get('grpc_target')}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_chat():
    """测试 AI 对话"""
    print("\n[测试 3] AI 对话 POST /api/chat")
    print("-" * 60)

    try:
        payload = {"message": "你好，这是一个测试消息"}
        print(f"请求: {payload}")

        response = httpx.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30.0  # 30秒超时
        )
        print(f"状态码: {response.status_code}")
        data = response.json()

        if data.get("success"):
            print(f"成功: {data.get('success')}")
            print(f"AI 回复: {data.get('message')}")
            if data.get("metadata"):
                metadata = data["metadata"]
                print(f"请求 ID: {metadata.get('request_id')}")
                print(f"模型: {metadata.get('model')}")
                print(f"耗时: {metadata.get('duration')} 秒")
        else:
            print(f"失败: {data.get('error')}")

        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_monitor_printer():
    """测试打印机监控"""
    print("\n[测试 4] 打印机监控 POST /api/monitor-printer")
    print("-" * 60)

    try:
        payload = {}  # 使用默认摄像头 URL
        print(f"请求: {payload}")

        response = httpx.post(
            f"{BASE_URL}/api/monitor-printer",
            json=payload,
            timeout=60.0  # 60秒超时（图像处理可能较慢）
        )
        print(f"状态码: {response.status_code}")
        data = response.json()

        if data.get("success"):
            print(f"成功: {data.get('success')}")
            print(f"检测到问题: {data.get('has_issues')}")
            if data.get('has_issues'):
                print(f"问题描述: {data.get('issue')}")
                print(f"处理建议: {data.get('suggestion')}")
            print(f"置信度: {data.get('confidence')}")
            print(f"总结: {data.get('summary')}")
        else:
            print(f"失败: {data.get('error')}")

        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("  Lumi Pilot HTTP Gateway 测试")
    print("=" * 60)
    print(f"\n目标服务器: {BASE_URL}")
    print(f"请确保以下服务已启动:")
    print(f"  1. gRPC 服务器 (python main.py)")
    print(f"  2. HTTP 网关 (uv run python -m http_gateway.server)")

    # 运行测试
    results = []
    results.append(("根路径", test_root()))
    results.append(("健康检查", test_health()))
    results.append(("AI 对话", test_chat()))
    results.append(("打印机监控", test_monitor_printer()))

    # 显示结果
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20s} {status}")

    # 统计
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\n总计: {passed_count}/{total_count} 通过")

    # 返回退出码
    sys.exit(0 if passed_count == total_count else 1)


if __name__ == "__main__":
    main()
