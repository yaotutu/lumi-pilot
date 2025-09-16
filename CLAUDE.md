# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

Lumi Pilot 是基于现代化架构构建的AI服务平台，支持多种AI服务和统一的接口层。该平台采用分层架构设计，支持CLI和gRPC两种接口方式，提供AI对话和故障检测等核心功能。

## 开发命令

### 依赖管理和环境
```bash
# 安装依赖
uv sync

# 安装开发依赖
uv sync --dev

# 运行AI对话服务
uv run lumi-pilot chat send "你的消息"
uv run lumi-pilot chat send "你的消息" --temperature 0.9 --max-tokens 200

# 运行故障检测服务
uv run lumi-pilot fault analyze-logs --logs "ERROR: Connection failed"
uv run lumi-pilot fault detect-anomaly metrics.json
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

### 应用程序命令
```bash
# 验证配置
uv run lumi-pilot validate

# 健康检查（所有服务）
uv run lumi-pilot health

# 显示当前配置
uv run lumi-pilot --config

# 列出所有可用服务
uv run lumi-pilot services
```

## 现代化架构设计

项目采用现代化的分层架构，支持多服务和统一接口：

### 架构层次

```
┌─────────────┬─────────────┐
│   CLI       │    gRPC     │  <- 接口层 (interfaces/)
│   Interface │  Interface  │
└─────────────┴─────────────┘
            │
┌───────────────────────────┐
│   Application Layer       │  <- 应用层 (core/)
│   - Service Registry      │
│   - Request Routing       │
└───────────────────────────┘
            │
    ┌───────┴───────┐
    │               │
┌─────────┐  ┌──────────────┐
│ Chat    │  │ Fault        │  <- 业务服务层 (services/)
│ Service │  │ Detection    │
│         │  │ Service      │
└─────────┘  └──────────────┘
            │
┌───────────────────────────┐
│   Infrastructure Layer    │  <- 基础设施层 (infrastructure/)
│   - LLM Client            │
│   - Config Management     │
│   - Logging System        │
└───────────────────────────┘
```

### 核心模块

**Core Layer** (`core/`):
- `application.py`: 应用核心和服务注册表
- `protocols.py`: 服务接口协议定义
- `models.py`: 统一数据模型

**Services Layer** (`services/`):
- `chat/`: AI对话服务模块
- `fault_detection/`: AI故障检测服务模块
- 每个服务都实现统一的AIService协议

**Infrastructure Layer** (`infrastructure/`):
- `llm/`: LLM客户端和提供商抽象
- `config/`: 配置管理和环境变量
- `logging/`: 结构化日志系统

**Interfaces Layer** (`interfaces/`):
- `cli/`: 命令行接口实现
- `grpc/`: gRPC接口实现（预留）

### 服务协议

所有业务服务都必须实现 `AIService` 协议：

```python
class AIService(Protocol):
    async def process(self, request: ServiceRequest) -> ServiceResponse:
        """处理服务请求"""
        ...
    
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        ...
    
    def get_service_name(self) -> str:
        """获取服务名称"""
        ...
    
    def get_supported_actions(self) -> list[str]:
        """获取支持的操作列表"""
        ...
```

### 统一数据模型

```python
# 服务请求模型
class ServiceRequest(BaseModel):
    action: str                          # 操作类型
    payload: Dict[str, Any]             # 请求数据
    context: Optional[RequestContext]    # 请求上下文
    metadata: Optional[Dict[str, Any]]   # 元数据

# 服务响应模型
class ServiceResponse(BaseModel):
    success: bool                        # 是否成功
    data: Optional[Dict[str, Any]]      # 响应数据
    error: Optional[str]                # 错误信息
    metadata: ResponseMetadata          # 响应元数据
```

## 支持的服务

### 1. AI对话服务 (Chat Service)

**支持的操作**:
- `chat`: 普通对话
- `stream_chat`: 流式对话

**CLI命令**:
```bash
# 基本对话
uv run lumi-pilot chat send "你好"

# 自定义参数
uv run lumi-pilot chat send "分析这个问题" --system-prompt "你是技术专家" --temperature 0.8

# 使用角色
uv run lumi-pilot chat send "帮我写代码" --character technical
```

### 2. AI故障检测服务 (Fault Detection Service)

**支持的操作**:
- `analyze_logs`: 日志分析
- `detect_anomaly`: 异常检测
- `diagnose_system`: 系统诊断

**CLI命令**:
```bash
# 日志分析
uv run lumi-pilot fault analyze-logs --logs "ERROR: Database connection failed" --log-type application

# 异常检测
uv run lumi-pilot fault detect-anomaly metrics.json --threshold 0.8

# 批量日志分析
uv run lumi-pilot fault analyze-logs --logs "Error 1" --logs "Error 2" --logs "Error 3"
```

## 环境变量

必需变量：
- `LUMI_OPENAI_API_KEY`: OpenAI API 密钥

可选变量：
- `LUMI_OPENAI_BASE_URL`: API 基础URL（默认: https://api.openai.com/v1）
- `LUMI_OPENAI_MODEL`: 模型名称（默认: gpt-3.5-turbo）
- `LUMI_TEMPERATURE`: 温度参数 0.0-2.0（默认: 0.7）
- `LUMI_MAX_TOKENS`: 最大token数（默认: 1000）
- `LUMI_LOG_LEVEL`: 日志级别（默认: INFO）
- `LUMI_DEBUG`: 启用调试模式

## 响应格式

所有服务响应都遵循标准化的JSON结构：

```json
{
  "status": "success|error",
  "code": 200,
  "message": "操作状态描述（如'AI对话成功'、'日志分析完成'）",
  "error": "错误信息或null",
  "data": {
    "message": "AI回复内容（对话服务）",
    "analysis_result": "分析结果（故障检测服务）",
    "model": "使用的模型名称",
    "input_length": 123,
    "response_length": 456
  },
  "metadata": {
    "app_name": "Lumi Pilot",
    "version": "0.2.0",
    "request_id": "uuid",
    "timestamp": "iso_datetime",
    "duration": 1.23,
    "service_name": "chat",
    "action": "chat"
  }
}
```

## 扩展指南

### 添加新服务

1. 在 `services/` 下创建新的服务目录
2. 实现 `AIService` 协议
3. 在 `interfaces/cli/commands.py` 中注册服务
4. 添加相应的CLI命令

示例：
```python
# services/new_service/service.py
class NewService:
    async def process(self, request: ServiceRequest) -> ServiceResponse:
        # 实现服务逻辑
        pass
    
    async def health_check(self) -> HealthStatus:
        # 实现健康检查
        pass

# 在create_application()中注册
registry.register("new_service", NewService(llm_client))
```

### gRPC支持

架构已为gRPC支持做好准备：

1. 定义 `.proto` 文件
2. 生成gRPC代码
3. 在 `interfaces/grpc/` 中实现gRPC服务
4. 复用现有的 `Application` 和服务层

## 编码标准

### 异步优先
- 所有服务接口都是异步的
- 使用 `async/await` 处理I/O操作
- CLI通过 `asyncio.run()` 调用异步函数

### 类型提示
- 使用完整的类型提示
- 利用 `Protocol` 定义接口
- 使用 `Pydantic` 进行数据验证

### 错误处理
- 服务层统一错误处理模式
- 使用 `ServiceResponse` 包装所有响应
- 在应用层捕获和处理异常

### 依赖注入
- 通过构造函数注入依赖
- 使用服务注册表管理服务实例
- 避免全局状态和硬编码依赖

## 项目结构

```
lumi-pilot/
├── core/                    # 核心应用层
│   ├── application.py       # 应用和服务注册表
│   ├── protocols.py         # 服务接口协议
│   └── models.py           # 统一数据模型
├── services/               # 业务服务层
│   ├── chat/              # AI对话服务
│   └── fault_detection/   # AI故障检测服务
├── infrastructure/        # 基础设施层
│   ├── llm/              # LLM客户端
│   ├── config/           # 配置管理
│   └── logging/          # 日志系统
├── interfaces/           # 接口层
│   ├── cli/             # CLI接口
│   └── grpc/            # gRPC接口（预留）
├── utils/               # 临时兼容性工具
└── main.py             # 应用入口点
```

这种架构设计确保了：
- **可扩展性**: 易于添加新服务和接口
- **可测试性**: 清晰的依赖注入和接口分离
- **可维护性**: 分层清晰，职责分离
- **高性能**: 异步优先设计
- **类型安全**: 完整的类型提示和验证