"""
实用工具处理器
"""
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class UtilityHandlers:
    """实用工具处理器"""
    
    @staticmethod
    def calculate_math(expression: str) -> str:
        """安全计算数学表达式"""
        logger.info("utility_handlers", f"计算数学表达式: {expression}")
        
        try:
            # 只允许安全的数学运算
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                raise ValueError("表达式包含不安全的字符")
            
            if '..' in expression:
                raise ValueError("表达式格式不正确")
            
            result = eval(expression, {"__builtins__": {}}, {})
            
            if not isinstance(result, (int, float)):
                raise ValueError("计算结果不是数字")
            
            result_str = str(result)
            logger.info("utility_handlers", f"计算结果: {result_str}")
            return result_str
            
        except Exception as e:
            error_msg = f"计算错误: {str(e)}"
            logger.error("utility_handlers", error_msg)
            return error_msg