# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

Lumi Pilot 是基于 LangChain 构建的AI对话系统，支持 OpenAI 兼容的 API。该应用程序提供命令行界面，用于AI对话并输出结构化的JSON格式响应。

## 开发命令

### 依赖管理和环境
```bash
# 安装依赖
uv sync

# 安装开发依赖
uv sync --dev

# 运行应用
uv run lumi-pilot "你的消息"
uv run lumi-pilot chat "你的消息" --temperature 0.9 --max-tokens 200
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

# 健康检查
uv run lumi-pilot health

# 显示当前配置
uv run lumi-pilot --config
```

## 架构设计

项目采用分层架构，各层职责清晰分离：

### 核心模块
- **cli/**: 基于 Click 框架的命令行界面
- **config/**: 使用 Pydantic 的配置管理
- **models/**: 基于 LangChain ChatOpenAI 的大模型客户端
- **services/**: 业务逻辑层（ChatService）
- **utils/**: 共享工具，包括结构化日志系统

### 关键组件

**配置系统** (`config/settings.py`):
- 使用 Pydantic 设置，支持环境变量验证
- 所有环境变量以 `LUMI_` 为前缀
- 必需变量: `LUMI_OPENAI_API_KEY`
- 可选变量: `LUMI_OPENAI_BASE_URL`, `LUMI_OPENAI_MODEL`, `LUMI_TEMPERATURE` 等

**大模型客户端** (`models/llm_client.py`):
- LangChain ChatOpenAI 的封装器
- 处理消息准备（SystemMessage + HumanMessage）
- 结构化的错误处理和响应格式化
- 支持每个请求的参数覆盖

**聊天服务** (`services/chat_service.py`):
- CLI 和 LLM 客户端之间的业务逻辑层
- 标准化的JSON响应格式：status/code/message/data/metadata
- 为AI助手提供中文默认系统提示词

**日志系统** (`utils/logger.py`):
- 使用 structlog 进行结构化日志记录
- 双重输出：控制台（彩色）和文件（JSON格式）
- 轮转文件处理器（10MB，5个备份）
- 专门的API调用和错误日志记录函数

### 响应格式

所有响应都遵循标准化的JSON结构：
```json
{
  "status": "success|error",
  "code": 200,
  "message": "响应内容",
  "data": {},
  "metadata": {
    "app_name": "Lumi Pilot",
    "version": "0.1.0",
    "timestamp": 1234567890
  }
}
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

## 编码标准

### 代码文档要求
**重要：所有代码都必须包含详细注释，说明以下内容：**

1. **函数/方法目的**：说明函数的作用和存在的原因
2. **参数说明**：详细描述每个参数的用途和期望值
3. **返回值**：说明返回的内容和格式
4. **业务逻辑**：复杂逻辑必须有内联注释
5. **错误处理**：解释捕获了哪些错误以及如何处理
6. **副作用**：任何文件操作、API调用或状态变更

### 注释标准
- 为所有函数、类和模块使用docstring
- 为复杂逻辑块添加内联注释
- 解释为什么这样做，而不仅仅是做了什么
- 在非平凡函数的docstring中包含示例
- 记录任何假设或限制

### 注释结构示例
```python
def process_user_message(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理用户消息并返回AI响应
    
    这是聊天服务的核心方法，负责：
    1. 验证输入消息的有效性
    2. 调用LLM客户端获取AI响应 
    3. 格式化响应为标准JSON结构
    
    Args:
        message: 用户输入的消息内容，不能为空字符串
        context: 对话上下文信息，包含会话ID、用户偏好等
        
    Returns:
        Dict[str, Any]: 标准化的响应格式，包含：
            - status: 'success' 或 'error'
            - message: AI回复内容或错误信息
            - data: 包含token使用量、耗时等元数据
            
    Raises:
        ValueError: 当message为空或格式无效时
        APIError: 当LLM API调用失败时
        
    Example:
        >>> process_user_message("你好", {"session_id": "123"})
        {"status": "success", "message": "你好！我是AI助手", ...}
    """
    # 验证输入参数 - 确保消息不为空
    if not message or not message.strip():
        # 返回错误响应而不是抛出异常，保持API稳定性
        return self._create_error_response("消息不能为空")
```

## 项目结构考虑

- 配置管理采用 Pydantic 进行集中化和验证
- 错误处理在各层之间遵循一致的模式
- CLI 支持直接消息输入和子命令两种方式
- 日志系统记录应用程序事件和详细的API调用信息
- 系统设计兼容任何 OpenAI 兼容的 API 端点
- **所有新代码都必须遵循上述详细的注释标准**