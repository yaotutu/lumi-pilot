# Lumi Pilot HTTP Gateway

**临时 HTTP 网关**，用于将 HTTP 请求转发到 Lumi Pilot gRPC 服务器。

> ⚠️ **注意**: 这是一个临时测试用的模块，后期可以完全删除，不会影响主项目。

## 架构说明

```
外部 HTTP 客户端
    ↓ HTTP JSON
HTTP Gateway (FastAPI)
    ↓ gRPC Protobuf
Lumi Pilot gRPC Server
    ↓
核心服务（Chat, PrinterMonitoring 等）
```

## 快速开始

### 1. 安装依赖

```bash
cd http_gateway
uv sync
```

### 2. 启动服务

**终端 1：启动 gRPC 服务器（必须先启动）**

```bash
cd /path/to/lumi-pilot
python main.py
```

**终端 2：启动 HTTP 网关**

```bash
cd /path/to/lumi-pilot/http_gateway

# 方式 1：使用 uv run
uv run python -m http_gateway.server

# 方式 2：使用 uvicorn
uv run uvicorn http_gateway.server:app --host 0.0.0.0 --port 8000

# 方式 3：使用 uv run + uvicorn（推荐）
uv run uvicorn http_gateway.server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问 API 文档

启动后访问自动生成的 Swagger 文档：

```
http://localhost:8000/docs
```

## API 端点

### 1. 根路径

```bash
GET /
```

返回服务信息和可用端点。

### 2. 健康检查

```bash
GET /health
```

**响应示例：**

```json
{
  "status": "healthy",
  "http_gateway": "running",
  "grpc_backend": "connected",
  "grpc_target": "localhost:50051",
  "timestamp": "2025-11-14T10:30:00.123456"
}
```

### 3. AI 对话

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "你好，Lumi Pilot"
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "你好！我是Lumi Pilot AI助手，很高兴为你服务。有什么我可以帮助你的吗？",
  "error": null,
  "metadata": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "model": "Pro/deepseek-ai/DeepSeek-V3",
    "duration": 2.35,
    "timestamp": "2025-11-14T10:30:02.456789"
  }
}
```

### 4. 打印机监控

```bash
POST /api/monitor-printer
Content-Type: application/json

{
  "camera_url": "http://192.168.1.100:8080/video"  # 可选
}
```

**响应示例（成功）：**

```json
{
  "success": true,
  "has_issues": false,
  "issue": "",
  "suggestion": "打印状态正常，继续监控",
  "confidence": "高",
  "summary": "打印机运行正常，未发现明显问题",
  "timestamp": "2025-11-14T10:35:00.123456",
  "error": null
}
```

**响应示例（检测到问题）：**

```json
{
  "success": true,
  "has_issues": true,
  "issue": "检测到打印件边缘有轻微翘边",
  "suggestion": "建议检查热床温度和第一层附着力",
  "confidence": "中",
  "summary": "打印过程中出现边缘翘边现象，可能影响打印质量",
  "timestamp": "2025-11-14T10:35:00.123456",
  "error": null
}
```

## 环境变量配置

可通过环境变量自定义配置：

```bash
# gRPC 服务器地址
export GRPC_HOST=localhost
export GRPC_PORT=50051

# HTTP 服务器配置
export HTTP_HOST=0.0.0.0
export HTTP_PORT=8000

# 启动服务
uv run python -m http_gateway.server
```

## 使用示例

### cURL

```bash
# 健康检查
curl http://localhost:8000/health

# AI 对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 打印机监控
curl -X POST http://localhost:8000/api/monitor-printer \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Python

```python
import requests

# AI 对话
response = requests.post(
    "http://localhost:8000/api/chat",
    json={"message": "你好，Lumi Pilot"}
)
result = response.json()
print(result["message"])

# 打印机监控
response = requests.post(
    "http://localhost:8000/api/monitor-printer",
    json={"camera_url": "http://192.168.1.100:8080/video"}
)
result = response.json()
if result["success"]:
    print(f"监控结果: {result['summary']}")
else:
    print(f"监控失败: {result['error']}")
```

### JavaScript / Fetch API

```javascript
// AI 对话
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: '你好，Lumi Pilot' })
});
const data = await response.json();
console.log(data.message);
```

## 测试脚本

查看 `tests/` 目录获取完整的测试示例。

```bash
# 运行测试（需要 httpx）
uv run python tests/test_api.py
```

## 项目结构

```
http_gateway/
├── pyproject.toml              # uv 项目配置
├── .python-version             # Python 版本锁定
├── README.md                   # 本文档
├── http_gateway/
│   ├── __init__.py
│   ├── server.py              # FastAPI 主服务器
│   ├── grpc_client.py         # gRPC 客户端封装
│   ├── models.py              # HTTP 数据模型
│   └── generated/             # 符号链接到主项目 generated/
└── tests/
    └── test_api.py            # API 测试脚本
```

## 技术栈

- **FastAPI**: 现代高性能 Web 框架
- **Uvicorn**: ASGI 服务器
- **gRPC**: 与主项目通信
- **Pydantic**: 数据验证和序列化
- **uv**: 依赖管理

## 错误处理

HTTP 网关会将 gRPC 错误转换为标准 HTTP 状态码：

- `503 Service Unavailable`: gRPC 服务器不可用或调用失败
- `500 Internal Server Error`: 内部错误
- `422 Unprocessable Entity`: 请求参数验证失败

## 删除方式

当不再需要 HTTP 网关时，直接删除整个目录即可：

```bash
cd /path/to/lumi-pilot
rm -rf http_gateway/
```

主项目完全不受影响，因为：
- HTTP 网关是独立的 uv 项目
- 有自己的依赖管理
- 使用符号链接引用主项目代码，无侵入性

## 常见问题

### Q: HTTP 网关无法连接到 gRPC 服务器？

**A**: 请确认：
1. gRPC 服务器已启动（`python main.py`）
2. gRPC 监听在 `localhost:50051`
3. 防火墙没有阻止连接

### Q: 如何更改端口？

**A**: 使用环境变量或命令行参数：

```bash
# 环境变量方式
HTTP_PORT=9000 uv run python -m http_gateway.server

# 命令行参数方式
uv run uvicorn http_gateway.server:app --port 9000
```

### Q: 如何启用 HTTPS？

**A**: 使用 uvicorn 的 SSL 选项：

```bash
uv run uvicorn http_gateway.server:app \
  --ssl-keyfile=/path/to/key.pem \
  --ssl-certfile=/path/to/cert.pem
```

## 许可证

与主项目保持一致。
