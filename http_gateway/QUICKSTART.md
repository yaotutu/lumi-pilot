# 快速开始指南

## 一、安装依赖

```bash
cd http_gateway
uv sync
```

## 二、启动服务

### 方式 1：手动启动（推荐用于开发和测试）

**终端 1 - 启动 gRPC 服务器：**

```bash
cd /path/to/lumi-pilot
uv run python main.py
```

**终端 2 - 启动 HTTP 网关：**

```bash
cd /path/to/lumi-pilot/http_gateway
uv run python -m http_gateway.server
```

### 方式 2：使用 uvicorn（支持热重载）

```bash
cd /path/to/lumi-pilot/http_gateway
uv run uvicorn http_gateway.server:app --host 0.0.0.0 --port 8000 --reload
```

## 三、访问服务

- **根路径**: http://localhost:8000/
- **API 文档（Swagger UI）**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 四、测试 API

### 使用 cURL

```bash
# 健康检查
curl http://localhost:8000/health

# AI 对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，Lumi Pilot"}'

# 打印机监控
curl -X POST http://localhost:8000/api/monitor-printer \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 使用测试脚本

```bash
cd /path/to/lumi-pilot/http_gateway
uv run python tests/test_api.py
```

## 五、环境变量配置（可选）

```bash
# gRPC 服务器地址
export GRPC_HOST=localhost
export GRPC_PORT=50051

# HTTP 服务器配置
export HTTP_HOST=0.0.0.0
export HTTP_PORT=8000
```

## 六、停止服务

按 `Ctrl+C` 停止服务器。

## 常见问题

### Q: 提示 "Address already in use"？
**A**: 端口被占用，使用以下命令杀死占用进程：
```bash
lsof -ti:8000 | xargs kill -9
```

### Q: 提示 "gRPC backend disconnected"？
**A**: gRPC 服务器未启动，请先启动 gRPC 服务器（终端 1）。

### Q: 如何更改端口？
**A**:
```bash
HTTP_PORT=9000 uv run python -m http_gateway.server
```
