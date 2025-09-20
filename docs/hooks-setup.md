# Claude Code Hooks 配置说明

## 概述
已配置自动化post-completion hook，在每次任务完成后自动运行代码质量检查和修复。

## 配置文件
- **Hook配置**: `.claude/settings.json` (项目级配置)
- **Hook脚本**: `scripts/post_completion_hook.py`
- **Ruff配置**: `ruff.toml`

## 工作流程

### 1. 触发时机
- 每次工具使用完成后自动触发 (PostToolUse)
- Claude完成代码编写、修改、重构等任务时

### 2. 执行步骤
1. **代码检查** - 运行 `ruff check .`
2. **问题展示** - 如果发现问题，显示前20个问题
3. **自动修复** - 运行 `ruff check --fix --unsafe-fixes .`
4. **再次检查** - 验证修复效果
5. **结果报告** - 显示最终状态

### 3. 输出示例
```
============================================================
🎯 [Post-Completion Hook] 任务完成后质量检查
============================================================
🔍 [Post-Completion Hook] 运行代码质量检查...
✅ [Post-Completion Hook] 代码质量检查通过，无需修复
🎉 [Post-Completion Hook] 质量检查完成，代码符合规范
============================================================
```

## 手动运行
如需手动触发hook：
```bash
python scripts/post_completion_hook.py
```

## 自定义配置
如需调整检查规则，编辑 `ruff.toml` 文件。

## 优势
- **自动化**: 无需手动记住运行代码检查
- **即时修复**: 大部分问题可自动修复
- **质量保障**: 确保提交的代码符合规范
- **开发效率**: 减少code review中的格式问题