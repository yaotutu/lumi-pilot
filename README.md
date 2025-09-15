# Lumi Pilot

基于LangChain的AI对话系统，支持OpenAI兼容接口。

## 功能特性

- 🤖 支持OpenAI兼容的API接口
- 📦 使用LangChain框架
- 🔧 完整的配置管理系统
- 📊 结构化日志记录
- 🖥️ 命令行界面(CLI)
- 📄 JSON格式输出

## 快速开始

### 1. 安装依赖

```bash
# 使用uv安装依赖
uv sync
```

### 2. 配置环境变量

将配置添加到你的shell配置文件（如~/.zshrc）：

```bash
export LUMI_OPENAI_API_KEY="your_api_key_here"         # 必需：API密钥
export LUMI_OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选：API基础URL
export LUMI_OPENAI_MODEL="gpt-3.5-turbo"             # 可选：要使用的模型
export LUMI_TEMPERATURE="0.7"                        # 可选：默认温度参数
export LUMI_MAX_TOKENS="1000"                        # 可选：默认最大token数
```

重新加载配置：
```bash
source ~/.zshrc
```

### 3. 验证配置

```bash
# 验证环境配置
uv run lumi-pilot validate

# 检查服务健康状态
uv run lumi-pilot health
```

### 4. 开始使用

```bash
# 直接对话
uv run lumi-pilot "你好，请介绍一下自己"

# 使用chat命令
uv run lumi-pilot chat "什么是人工智能？"

# 自定义参数
uv run lumi-pilot chat "写一首诗" --temperature 0.9 --max-tokens 200

# 使用自定义系统提示词
uv run lumi-pilot chat "解释量子计算" --system-prompt "你是一位物理学教授"

# 组合使用多个参数
uv run lumi-pilot chat "创作一个科幻故事" --temperature 0.8 --max-tokens 500
```

## 命令行选项

### 全局选项

- `--debug`: 启用调试模式
- `--config`: 显示当前配置

### chat命令选项

- `--system-prompt, -s`: 自定义系统提示词
- `--temperature, -t`: 温度参数 (0.0-2.0)
- `--max-tokens, -m`: 最大token数
- `--format, -f`: 输出格式 (json/text)

## 环境变量

| 变量名 | 描述 | 默认值 | 示例 |
|--------|------|--------|------|
| `LUMI_OPENAI_API_KEY` | OpenAI API密钥 | **必需** | `sk-...` |
| `LUMI_OPENAI_BASE_URL` | API基础URL | `https://api.openai.com/v1` | `https://api.deepseek.com/v1` |
| `LUMI_OPENAI_MODEL` | 使用的模型 | `gpt-3.5-turbo` | `gpt-4`, `deepseek-chat` |
| `LUMI_MAX_TOKENS` | 最大token数 | `1000` | `2000` |
| `LUMI_TEMPERATURE` | 温度参数 | `0.7` | `0.3`, `0.9` |
| `LUMI_LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`, `WARNING` |
| `LUMI_DEBUG` | 调试模式 | `false` | `true` |

**注意**: 模型选择通过 `LUMI_OPENAI_MODEL` 环境变量设置，支持任何OpenAI兼容的模型名称。

## 输出格式

默认输出为JSON格式，包含以下字段：

```json
{
  "status": "success",
  "code": 200,
  "message": "AI回复内容",
  "data": {
    "model": "gpt-3.5-turbo",
    "input_length": 10,
    "response_length": 50,
    "duration": 1.23
  },
  "metadata": {
    "app_name": "Lumi Pilot",
    "version": "0.1.0",
    "timestamp": 1234567890
  }
}
```

## 项目结构

```
lumi-pilot/
├── lumi_pilot/          # 主要代码
│   ├── cli/            # CLI相关
│   ├── config/         # 配置管理
│   ├── models/         # 大模型客户端
│   ├── services/       # 业务逻辑
│   └── utils/          # 工具函数
├── logs/               # 日志文件
├── tests/              # 测试文件
└── pyproject.toml      # 项目配置
```

## 开发

### 安装开发依赖

```bash
uv sync --dev
```

### 代码格式化

```bash
uv run black lumi_pilot/
uv run ruff check lumi_pilot/
```

### 类型检查

```bash
uv run mypy lumi_pilot/
```

## 后续计划

- [ ] 添加gRPC服务器支持
- [ ] 实现MCP (Model Context Protocol) 调用
- [ ] 添加对话上下文管理
- [ ] 支持流式响应
- [ ] 添加更多输出格式