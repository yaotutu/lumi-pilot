#!/usr/bin/env python3
"""
Post-completion Hook: 任务完成后自动代码质量检查和修复
在任务完成后自动运行ruff检查，如果发现问题则尝试自动修复
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_and_fix_code():
    """检查并修复代码质量问题"""
    project_root = Path(__file__).parent.parent

    print("🔍 [Post-Completion Hook] 运行代码质量检查...")

    # 首先检查是否有问题
    returncode, stdout, stderr = run_command("uv run ruff check .", cwd=project_root)

    if returncode == 0:
        print("✅ [Post-Completion Hook] 代码质量检查通过，无需修复")
        return True

    # 如果有问题，显示问题并尝试自动修复
    print("⚠️  [Post-Completion Hook] 发现代码质量问题:")
    if stderr:
        # 只显示前5个问题，避免输出过长
        error_lines = stderr.split('\n')[:20]
        print('\n'.join(error_lines))
        if len(stderr.split('\n')) > 20:
            print("... (更多问题)")

    print("\n🔧 [Post-Completion Hook] 尝试自动修复...")

    # 尝试自动修复
    fix_returncode, fix_stdout, fix_stderr = run_command(
        "uv run ruff check --fix --unsafe-fixes .", 
        cwd=project_root
    )

    # 再次检查是否还有问题
    final_returncode, final_stdout, final_stderr = run_command("uv run ruff check .", cwd=project_root)

    if final_returncode == 0:
        print("✅ [Post-Completion Hook] 代码质量问题已自动修复完成")
        return True
    else:
        print("⚠️  [Post-Completion Hook] 部分问题需要手动修复:")
        if final_stderr:
            # 只显示剩余的前3个问题
            remaining_lines = final_stderr.split('\n')[:10]
            print('\n'.join(remaining_lines))
        print("\n💡 建议运行: uv run ruff check --fix .")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🎯 [Post-Completion Hook] 任务完成后质量检查")
    print("="*60)

    try:
        success = check_and_fix_code()

        if success:
            print("🎉 [Post-Completion Hook] 质量检查完成，代码符合规范")
        else:
            print("📝 [Post-Completion Hook] 质量检查完成，但仍有部分问题需要注意")

    except Exception as e:
        print(f"❌ [Post-Completion Hook] 执行失败: {e}")
        return 1

    print("="*60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
