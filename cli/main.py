"""
Lumi Pilot CLI 主入口
提供命令行接口来使用AI对话功能
"""
import json
import sys
from typing import Optional

import click

from utils.logger import setup_logging, get_logger
from config.settings import get_settings, validate_environment, print_current_config
from services.chat_service import ChatService


def init_app(enable_console_log: bool = True) -> bool:
    """
    初始化应用
    
    Args:
        enable_console_log: 是否启用控制台日志
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        # 获取配置
        settings = get_settings()
        
        # 设置日志
        setup_logging(
            log_level=settings.log_level,
            log_file=settings.log_file,
            enable_console=enable_console_log and settings.enable_console_log,
            enable_file=settings.enable_file_log,
        )
        
        logger = get_logger(__name__)
        logger.info("Lumi Pilot 启动", version="0.1.0")
        
        return True
        
    except Exception as e:
        print(f"应用初始化失败: {e}", file=sys.stderr)
        return False


@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.option('--config', is_flag=True, help='显示当前配置')
@click.pass_context
def cli(ctx: click.Context, debug: bool, config: bool):
    """
    Lumi Pilot - AI对话系统
    
    使用示例:
    lumi-pilot "你好，请介绍一下自己"
    lumi-pilot chat "什么是人工智能？"
    """
    # 设置调试模式
    if debug:
        import os
        os.environ['LUMI_DEBUG'] = 'true'
    
    # 检查是否为JSON输出模式
    json_mode = len(sys.argv) > 2 and '--format' in sys.argv and sys.argv[sys.argv.index('--format') + 1] == 'json'
    
    # 初始化应用
    if not init_app(enable_console_log=not json_mode):
        sys.exit(1)
    
    # 显示配置
    if config:
        print_current_config()
        return
    
    # 如果没有子命令且有参数，直接进行对话
    if ctx.invoked_subcommand is None:
        # 检查是否有参数传入
        if len(sys.argv) > 1 and not any(arg.startswith('--') for arg in sys.argv[1:]):
            # 获取所有非选项参数作为消息
            message = ' '.join(arg for arg in sys.argv[1:] if not arg.startswith('--'))
            if message:
                _quick_chat(message)
                return
        
        # 否则显示帮助
        click.echo(ctx.get_help())


@cli.command()
@click.argument('message', required=True)
@click.option('--system-prompt', '-s', help='自定义系统提示词')
@click.option('--temperature', '-t', type=float, help='温度参数 (0.0-2.0)')
@click.option('--max-tokens', '-m', type=int, help='最大token数')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='json', help='输出格式')
@click.pass_context
def chat(ctx: click.Context, message: str, system_prompt: Optional[str], temperature: Optional[float], 
         max_tokens: Optional[int], format: str):
    """
    发送消息进行AI对话
    
    MESSAGE: 要发送的消息内容
    """
    # chat命令不需要重新初始化，在主入口点已处理
    
    _process_chat(message, system_prompt, temperature, max_tokens, format)


@cli.command()
def health():
    """检查服务健康状态"""
    try:
        chat_service = ChatService()
        result = chat_service.health_check()
        
        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 根据状态设置退出码
        if result.get('status') != 'healthy':
            sys.exit(1)
            
    except Exception as e:
        error_result = {
            "status": "error",
            "code": 500,
            "message": "",
            "error": f"健康检查失败: {str(e)}",
            "data": {}
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


@cli.command()
def validate():
    """验证环境配置"""
    is_valid, errors = validate_environment()
    
    result = {
        "status": "valid" if is_valid else "invalid",
        "code": 200 if is_valid else 400,
        "message": "环境配置有效" if is_valid else "环境配置无效",
        "data": {
            "errors": errors
        }
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not is_valid:
        sys.exit(1)


def _quick_chat(message: str):
    """快速对话（不使用子命令）"""
    _process_chat(message, format='json')


def _process_chat(
    message: str, 
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    format: str = 'json'
):
    """
    处理对话请求
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词
        temperature: 温度参数
        max_tokens: 最大token数
        format: 输出格式
    """
    try:
        # 验证环境
        is_valid, errors = validate_environment()
        if not is_valid:
            error_result = {
                "status": "error",
                "code": 400,
                "message": "",
                "error": f"环境配置无效: {'; '.join(errors)}",
                "data": {}
            }
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
            sys.exit(1)
        
        # 创建聊天服务
        chat_service = ChatService()
        
        # 准备参数
        kwargs = {}
        if temperature is not None:
            kwargs['temperature'] = temperature
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        
        # 处理消息
        result = chat_service.process_message(
            user_input=message,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 输出结果
        if format == 'json':
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # 文本格式输出
            if result.get('status') == 'success':
                print(result.get('message', ''))
            else:
                print(f"错误: {result.get('error', '未知错误')}", file=sys.stderr)
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(130)
    except Exception as e:
        error_result = {
            "status": "error",
            "code": 500,
            "message": "",
            "error": f"处理失败: {str(e)}",
            "data": {}
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    cli()