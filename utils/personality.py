"""
人物角色管理模块
简化版角色管理器，只加载单个角色文件
"""
from typing import Dict, Any, Optional
from .character_loader import CharacterLoader


class PersonalityManager:
    """人物角色管理器"""
    
    def __init__(self, character_file: str = None):
        """
        初始化人物角色管理器
        
        Args:
            character_file: 角色配置文件路径
        """
        # 在启动时加载单个角色数据
        self.loader = CharacterLoader(character_file)
    
    def get_system_prompt(self) -> str:
        """
        获取角色的系统提示词
        
        Returns:
            str: 系统提示词
        """
        return self.loader.get_system_prompt()
    
    def get_character_name(self) -> str:
        """
        获取角色名称
        
        Returns:
            str: 角色名称
        """
        return self.loader.get_character_name()
    
    def get_character_info(self) -> Dict[str, Any]:
        """
        获取角色信息
        
        Returns:
            Dict[str, Any]: 角色信息
        """
        return self.loader.get_character_data()


# 全局实例
_personality_manager = None


def get_personality_manager(character_file: str = None) -> PersonalityManager:
    """
    获取人物角色管理器实例
    
    Args:
        character_file: 角色配置文件路径
    
    Returns:
        PersonalityManager: 管理器实例
    """
    global _personality_manager
    if _personality_manager is None:
        _personality_manager = PersonalityManager(character_file)
    return _personality_manager