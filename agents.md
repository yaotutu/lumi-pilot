# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

Lumi Pilot 是基于现代化架构构建的AI服务平台。项目采用分层架构设计，**默认启动gRPC服务**，为外部客户端提供AI对话服务。支持CLI管理和gRPC接口两种使用方式。

## 快速启动

### 主要启动方式
```bash
# 默认启动gRPC服务器（推荐）
python main.py
# 或
uv run main.py
```

### 管理命令（可选）
```bash
# CLI管理功能
uv run lumi-pilot chat send "你的消息"
uv run lumi-pilot grpc serve
uv run lumi-pilot health
uv run lumi-pilot --config
```

**注意**: 系统提示词和角色配置完全由系统内部管理，不允许外部传入或覆盖。

## 开发命令

### 依赖管理
```bash
# 安装依赖
uv sync

# 安装开发依赖
uv sync --dev
```

### 代码质量检查
```bash
# 代码格式化
uv run black lumi_pilot/

# 代码检查  
uv run ruff check lumi_pilot/

# 类型检查
uv run mypy lumi_pilot/
```

## 项目架构

### 现代化分层设计

```
lumi-pilot/
├── main.py                         # 默认启动入口 - 直接启动gRPC服务器
├── protos/lumi_pilot.proto         # gRPC接口定义（供各语言客户端使用）
├── generated/                      # 自动生成的gRPC代码
├── examples/                       # 客户端调用示例
│   ├── python_client.py           # Python客户端示例
│   └── other_languages.md         # 其他语言调用指南
├── core/                          # 核心应用层
│   ├── application.py             # 应用和服务注册表
│   ├── protocols.py               # 服务接口协议
│   └── models.py                  # 统一数据模型
├── services/                      # 业务服务层
│   ├── chat/                      # AI对话服务
│   └── fault_detection/           # AI故障检测服务
├── infrastructure/               # 基础设施层
│   ├── llm/                      # LLM客户端
│   ├── config/                   # 配置管理
│   └── logging/                  # 日志系统
└── interfaces/                   # 接口层
    ├── cli/                      # CLI接口（管理用）
    └── grpc/                     # gRPC接口（主要服务）
```

### 服务架构层次

```
┌─────────────────────────────────┐
│         gRPC Interface          │  <- 主要接口（默认启动）
│    localhost:50051              │
└─────────────────────────────────┘
            │
┌─────────────────────────────────┐
│     Application Layer           │  <- 应用层
│   - Service Registry            │
│   - Unified Request Routing     │
└─────────────────────────────────┘
            │
    ┌───────┴───────┐
┌─────────┐  ┌──────────────┐
│ Chat    │  │ Fault        │      <- 业务服务层  
│ Service │  │ Detection    │
└─────────┘  └──────────────┘
            │
┌─────────────────────────────────┐
│   Infrastructure Layer          │  <- 基础设施层
│   - LLM Client (DeepSeek-V3)   │
│   - Structured Logging         │
│   - Configuration Management   │
└─────────────────────────────────┘
```

## gRPC接口

### 服务定义
- **服务名**: `lumi_pilot.LumiPilotService`
- **方法**: `Chat(ChatRequest) returns (ChatResponse)`  
- **地址**: `localhost:50051`

### 接口协议
```protobuf
service LumiPilotService {
  rpc Chat(ChatRequest) returns (ChatResponse);
}

message ChatRequest {
  string message = 1;                    // 用户消息
}

message ChatResponse {
  bool success = 1;                      // 是否成功
  string message = 2;                    // AI回复内容
  string error = 3;                      // 错误信息
  ResponseMetadata metadata = 4;         // 元数据
}
```

### 客户端调用示例

**Python**:
```python
import grpc
from generated import lumi_pilot_pb2, lumi_pilot_pb2_grpc

with grpc.insecure_channel('localhost:50051') as channel:
    client = lumi_pilot_pb2_grpc.LumiPilotServiceStub(channel)
    request = lumi_pilot_pb2.ChatRequest(message="你好")
    response = client.Chat(request)
    print(response.message)
```

**其他语言**: 参考 `examples/other_languages.md`

## 系统提示词管理

### 设计理念
- **统一管理**: 系统提示词由系统内部统一管理，确保一致性
- **禁止覆盖**: 不允许外部客户端传入自定义系统提示词或角色参数
- **简化接口**: 客户端只需要发送用户消息，无需关心系统级配置

### 当前配置
```
系统提示词: "你是Lumi Pilot AI助手，一个智能、友好、专业的对话AI。请用中文回复，保持回答简洁明了，准确有用。"
```

### 实现位置
- **配置文件**: `services/chat/service.py:28`
- **应用逻辑**: ChatService 构造函数中设置统一的系统提示词
- **调用时机**: 每次 LLM 调用时自动添加系统消息

## 日志系统

### 日志格式
```
时间戳 [级别] [标签] 消息内容
```

### 典型日志流程
```
2025-09-16T07:36:50.134588Z [info] [grpc_chat] 收到对话请求: 你好
2025-09-16T07:36:50.135030Z [info] [llm_client] 调用API: Pro/deepseek-ai/DeepSeek-V3
2025-09-16T07:36:52.338354Z [info] [llm_client] API调用成功: Pro/deepseek-ai/DeepSeek-V3, 耗时2.20s
2025-09-16T07:36:52.338758Z [info] [grpc_chat] 返回AI回复: 你好！我是Lumi Pilot AI助手...
```

## 环境变量

### 必需变量
- `LUMI_OPENAI_API_KEY`: OpenAI API 密钥

### 可选变量  
- `LUMI_OPENAI_BASE_URL`: API基础URL（默认: https://api.openai.com/v1）
- `LUMI_OPENAI_MODEL`: 模型名称（默认: gpt-3.5-turbo）
- `LUMI_TEMPERATURE`: 温度参数（默认: 0.7）
- `LUMI_MAX_TOKENS`: 最大token数（默认: 1000）
- `LUMI_LOG_LEVEL`: 日志级别（默认: INFO）
- `LUMI_DEBUG`: 启用调试模式

## 响应格式

所有gRPC响应遵循统一结构：

```json
{
  "success": true,
  "message": "AI回复内容",
  "error": "",
  "metadata": {
    "request_id": "uuid",
    "model": "Pro/deepseek-ai/DeepSeek-V3",
    "duration": 2.20,
    "timestamp": "2025-09-16T07:36:52.338354Z"
  }
}
```

## 扩展指南

### 添加新服务
1. 在 `services/` 创建新服务模块
2. 实现 `AIService` 协议
3. 在 `core/application.py` 中注册服务
4. 可选：添加CLI命令支持

### gRPC接口扩展
1. 修改 `protos/lumi_pilot.proto`
2. 重新生成代码: `python -m grpc_tools.protoc --python_out=generated --grpc_python_out=generated --proto_path=protos protos/lumi_pilot.proto`
3. 更新 `interfaces/grpc/handlers.py`

## 核心设计原则

### 简化优先
- **单一入口**: `python main.py` 直接启动服务
- **简洁接口**: gRPC客户端只需发送 `message` 字段
- **统一架构**: 所有服务共享统一的处理流程
- **系统接管**: 系统提示词和角色配置由系统内部统一管理

### 异步优先  
- 所有服务接口都是异步的
- 使用 `async/await` 处理I/O操作
- gRPC通过事件循环桥接异步服务

### 类型安全
- 使用 `Protocol` 定义服务接口
- 完整的类型提示和验证
- Pydantic模型确保数据一致性

### 依赖注入
- 通过服务注册表管理依赖
- 构造函数注入，避免全局状态
- 便于单元测试和模块替换

## 开发工作流

1. **启动开发服务器**: `python main.py`
2. **测试gRPC接口**: `python examples/python_client.py`  
3. **添加新功能**: 在相应的服务模块中实现
4. **代码质量检查**: `uv run ruff check . && uv run mypy .`
5. **提交代码**: 遵循项目的Git工作流

这种架构确保了：
- **易用性**: 一条命令启动完整AI服务
- **可扩展性**: 清晰的分层便于添加新功能  
- **可维护性**: 统一的接口和数据模型
- **高性能**: 异步架构和gRPC协议
- **多语言支持**: 标准gRPC接口支持各种客户端