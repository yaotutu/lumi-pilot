"""
人物角色管理模块（临时兼容性实现）
为了保持CLI的兼容性而保留
"""
from typing import Dict, Any, List


class PersonalityManager:
    """人物角色管理器"""
    
    def __init__(self):
        """初始化人物角色管理器"""
        self.characters = {
            "default": {
                "name": "默认助手",
                "description": "智能、友好、专业的AI助手",
                "system_prompt": "你是Lumi Pilot AI助手，一个智能、友好、专业的对话AI。请用中文回复，保持回答简洁明了，准确有用。"
            },
            "technical": {
                "name": "技术专家",
                "description": "专业的技术顾问和问题解决专家",
                "system_prompt": "你是一位经验丰富的技术专家，擅长分析和解决各种技术问题。请提供准确、专业的技术建议，并用中文回复。"
            }
        }
    
    def get_system_prompt(self, character: str) -> str:
        """
        获取角色的系统提示词
        
        Args:
            character: 角色名称
            
        Returns:
            str: 系统提示词
        """
        if character in self.characters:
            return self.characters[character]["system_prompt"]
        else:
            return self.characters["default"]["system_prompt"]
    
    def list_available_characters(self) -> List[str]:
        """
        获取可用角色列表
        
        Returns:
            List[str]: 角色名称列表
        """
        return list(self.characters.keys())
    
    def get_character_info(self, character: str) -> Dict[str, Any]:
        """
        获取角色信息
        
        Args:
            character: 角色名称
            
        Returns:
            Dict[str, Any]: 角色信息
        """
        return self.characters.get(character, self.characters["default"])


# 全局实例
_personality_manager = PersonalityManager()


def get_personality_manager() -> PersonalityManager:
    """
    获取人物角色管理器实例
    
    Returns:
        PersonalityManager: 管理器实例
    """
    return _personality_manager