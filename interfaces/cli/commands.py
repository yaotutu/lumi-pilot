"""
现代化CLI接口实现
基于新架构的命令行界面
"""
import asyncio
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any

import click

from infrastructure.logging import setup_logging, get_logger
from infrastructure.config import get_settings, validate_environment, print_current_config
from infrastructure.llm import LLMClient
from services.chat import ChatService
from services.fault_detection import FaultDetectionService
from core.application import Application, ServiceRegistry
from core.models import ServiceRequest
from utils.personality import get_personality_manager

# 初始化模块logger
logger = get_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_json_dumps(data: Dict[str, Any], **kwargs) -> str:
    """安全的JSON序列化，处理datetime对象"""
    return json.dumps(data, cls=DateTimeEncoder, **kwargs)


async def create_application() -> Application:
    """
    创建应用实例
    
    Returns:
        Application: 配置好的应用实例
    """
    # 获取配置
    settings = get_settings()
    
    # 创建基础设施
    llm_client = LLMClient()
    
    # 创建服务注册表
    registry = ServiceRegistry()
    
    # 注册服务
    registry.register("chat", ChatService(llm_client))
    registry.register("fault_detection", FaultDetectionService(llm_client))
    
    # 创建应用
    return Application(registry)


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
        
        logger.info("app", "Lumi Pilot 启动")
        
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
    Lumi Pilot - 现代化AI服务平台
    
    支持AI对话、故障检测等多种AI服务
    
    使用示例:
    lumi-pilot chat "你好，请介绍一下自己"
    lumi-pilot fault analyze-logs --logs "error.log"
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
    
    # 如果没有子命令，显示帮助
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.group()
def chat():
    """AI对话相关命令"""
    pass


@chat.command()
@click.argument('message', required=True)
@click.option('--system-prompt', '-s', help='自定义系统提示词')
@click.option('--character', '-c', help='选择人物角色')
@click.option('--temperature', '-t', type=float, help='温度参数 (0.0-2.0)')
@click.option('--max-tokens', '-m', type=int, help='最大token数')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='json', help='输出格式')
def send(message: str, system_prompt: Optional[str], character: Optional[str], 
         temperature: Optional[float], max_tokens: Optional[int], format: str):
    """
    发送消息进行AI对话
    
    MESSAGE: 要发送的消息内容
    """
    asyncio.run(_handle_chat_send(message, system_prompt, character, temperature, max_tokens, format))


@cli.group()
def fault():
    """故障检测相关命令"""
    pass


@fault.command()
@click.option('--logs', multiple=True, help='日志内容或文件路径')
@click.option('--log-type', default='application', help='日志类型')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='json', help='输出格式')
def analyze_logs(logs, log_type: str, format: str):
    """
    分析日志内容，检测潜在问题
    
    示例:
    lumi-pilot fault analyze-logs --logs "ERROR: Connection failed" --logs "WARN: High memory usage"
    """
    if not logs:
        click.echo("错误: 请提供日志内容", err=True)
        sys.exit(1)
    
    asyncio.run(_handle_fault_analyze_logs(list(logs), log_type, format))


@fault.command()
@click.argument('metrics_file', type=click.File('r'))
@click.option('--threshold', type=float, default=0.8, help='异常检测阈值')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='json', help='输出格式')
def detect_anomaly(metrics_file, threshold: float, format: str):
    """
    检测系统指标异常
    
    METRICS_FILE: 包含系统指标的JSON文件
    """
    try:
        metrics = json.load(metrics_file)
    except json.JSONDecodeError as e:
        click.echo(f"错误: 无效的JSON文件: {e}", err=True)
        sys.exit(1)
    
    asyncio.run(_handle_fault_detect_anomaly(metrics, threshold, format))


@cli.command()
def health():
    """检查所有服务健康状态"""
    asyncio.run(_handle_health_check())


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
    
    print(safe_json_dumps(result, ensure_ascii=False, indent=2))
    
    if not is_valid:
        sys.exit(1)


@cli.command()
def services():
    """列出所有可用服务"""
    asyncio.run(_handle_list_services())


async def _handle_chat_send(
    message: str, 
    system_prompt: Optional[str] = None,
    character: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    format: str = 'json'
):
    """处理聊天发送请求"""
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
            print(safe_json_dumps(error_result, ensure_ascii=False, indent=2))
            sys.exit(1)
        
        # 创建应用
        app = await create_application()
        
        # 准备请求数据
        payload = {
            "message": message,
            "system_prompt": system_prompt,
            "character": character
        }
        
        if temperature is not None:
            payload['temperature'] = temperature
        if max_tokens is not None:
            payload['max_tokens'] = max_tokens
        
        # 创建服务请求
        request = ServiceRequest(
            action="chat",
            payload=payload
        )
        
        # 执行请求
        response = await app.execute("chat", request)
        
        # 输出结果
        if format == 'json':
            result = {
                "status": "success" if response.success else "error",
                "code": 200 if response.success else 500,
                "message": "AI对话成功" if response.success else "AI对话失败",
                "error": response.error if not response.success else None,
                "data": response.data if response.success else {},
                "metadata": response.metadata.dict()
            }
            print(safe_json_dumps(result, ensure_ascii=False, indent=2))
        else:
            if response.success:
                print(response.data.get("message", ""))
            else:
                print(f"错误: {response.error}", file=sys.stderr)
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
        print(safe_json_dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


async def _handle_fault_analyze_logs(logs: list, log_type: str, format: str):
    """处理日志分析请求"""
    try:
        app = await create_application()
        
        request = ServiceRequest(
            action="analyze_logs",
            payload={
                "logs": logs,
                "log_type": log_type
            }
        )
        
        response = await app.execute("fault_detection", request)
        
        result = {
            "status": "success" if response.success else "error",
            "code": 200 if response.success else 500,
            "message": "日志分析完成" if response.success else "日志分析失败",
            "error": response.error if not response.success else None,
            "data": response.data if response.success else {},
            "metadata": response.metadata.dict()
        }
        
        if format == 'json':
            print(safe_json_dumps(result, ensure_ascii=False, indent=2))
        else:
            if response.success:
                print(response.data.get("analysis_result", ""))
            else:
                print(f"错误: {response.error}", file=sys.stderr)
                sys.exit(1)
                
    except Exception as e:
        error_result = {
            "status": "error",
            "code": 500,
            "error": f"日志分析失败: {str(e)}",
            "data": {}
        }
        print(safe_json_dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


async def _handle_fault_detect_anomaly(metrics: Dict[str, Any], threshold: float, format: str):
    """处理异常检测请求"""
    try:
        app = await create_application()
        
        request = ServiceRequest(
            action="detect_anomaly",
            payload={
                "metrics": metrics,
                "threshold": threshold
            }
        )
        
        response = await app.execute("fault_detection", request)
        
        result = {
            "status": "success" if response.success else "error",
            "code": 200 if response.success else 500,
            "message": "异常检测完成" if response.success else "异常检测失败",
            "error": response.error if not response.success else None,
            "data": response.data if response.success else {},
            "metadata": response.metadata.dict()
        }
        
        if format == 'json':
            print(safe_json_dumps(result, ensure_ascii=False, indent=2))
        else:
            if response.success:
                print(response.data.get("anomaly_analysis", ""))
            else:
                print(f"错误: {response.error}", file=sys.stderr)
                sys.exit(1)
                
    except Exception as e:
        error_result = {
            "status": "error",
            "code": 500,
            "error": f"异常检测失败: {str(e)}",
            "data": {}
        }
        print(safe_json_dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


async def _handle_health_check():
    """处理健康检查请求"""
    try:
        app = await create_application()
        health_result = await app.health_check()
        
        result = {
            "status": "healthy" if health_result["application_healthy"] else "unhealthy",
            "code": 200 if health_result["application_healthy"] else 503,
            "message": "所有服务正常" if health_result["application_healthy"] else "部分服务异常",
            "data": health_result
        }
        
        print(safe_json_dumps(result, ensure_ascii=False, indent=2))
        
        if not health_result["application_healthy"]:
            sys.exit(1)
            
    except Exception as e:
        error_result = {
            "status": "error",
            "code": 500,
            "error": f"健康检查失败: {str(e)}",
            "data": {}
        }
        print(safe_json_dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


async def _handle_list_services():
    """处理服务列表请求"""
    try:
        app = await create_application()
        services = app.registry.list_services()
        
        result = {
            "status": "success",
            "code": 200,
            "message": "可用服务列表",
            "data": {
                "services": []
            }
        }
        
        for service_name in services:
            service = app.registry.get(service_name)
            result["data"]["services"].append({
                "name": service_name,
                "display_name": service.get_service_name(),
                "supported_actions": service.get_supported_actions()
            })
        
        print(safe_json_dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        error_result = {
            "status": "error",
            "code": 500,
            "error": f"获取服务列表失败: {str(e)}",
            "data": {}
        }
        print(safe_json_dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    cli()