"""
人物角色管理模块
简化版角色管理器，在启动时加载所有角色数据
"""
from typing import Dict, Any, List
from .character_loader import CharacterLoader


class PersonalityManager:
    """人物角色管理器"""
    
    def __init__(self, characters_dir: str = None):
        """
        初始化人物角色管理器
        
        Args:
            characters_dir: 角色配置文件目录路径
        """
        # 在启动时加载所有角色数据
        self.loader = CharacterLoader(characters_dir)
    
    def get_system_prompt(self, character: str) -> str:
        """
        获取角色的系统提示词
        
        Args:
            character: 角色名称
            
        Returns:
            str: 系统提示词
        """
        return self.loader.format_system_prompt(character)
    
    def list_available_characters(self) -> List[str]:
        """
        获取可用角色列表
        
        Returns:
            List[str]: 角色名称列表
        """
        return self.loader.get_available_characters()
    
    def get_character_info(self, character: str) -> Dict[str, Any]:
        """
        获取角色信息
        
        Args:
            character: 角色名称
            
        Returns:
            Dict[str, Any]: 角色信息
        """
        return self.loader.get_character(character)


# 全局实例
_personality_manager = None


def get_personality_manager(characters_dir: str = None) -> PersonalityManager:
    """
    获取人物角色管理器实例
    
    Args:
        characters_dir: 角色配置文件目录路径
    
    Returns:
        PersonalityManager: 管理器实例
    """
    global _personality_manager
    if _personality_manager is None:
        _personality_manager = PersonalityManager(characters_dir)
    return _personality_manager