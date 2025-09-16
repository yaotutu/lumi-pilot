"""
人物系统模块
轻量级人物刻画实现，通过配置文件和系统提示词实现人物特色
"""
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .logger import get_logger

# 初始化模块logger
logger = get_logger(__name__)


class PersonalityManager:
    """
    人物管理器
    负责加载人物配置和生成个性化的系统提示词
    """
    
    def __init__(self, characters_dir: str = "characters"):
        """
        初始化人物管理器
        
        Args:
            characters_dir: 人物配置文件目录
        """
        self.characters_dir = Path(characters_dir)
        self.characters_cache = {}
        logger.info("personality", f"管理器初始化: {characters_dir}")
    
    def load_character(self, character_name: str) -> Dict[str, Any]:
        """
        加载指定人物配置
        
        Args:
            character_name: 人物名称（不含扩展名）
            
        Returns:
            人物配置字典
        """
        # 检查缓存
        if character_name in self.characters_cache:
            return self.characters_cache[character_name]
        
        # 加载配置文件
        config_path = self.characters_dir / f"{character_name}.yaml"
        
        if not config_path.exists():
            logger.error("personality", f"配置文件不存在: {character_name}")
            return self._get_default_character()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 缓存配置
            self.characters_cache[character_name] = config
            
            logger.info("personality", f"配置加载成功: {character_name}")
            
            return config
            
        except Exception as e:
            logger.error("personality", f"配置加载失败: {character_name} - {str(e)}")
            return self._get_default_character()
    
    def get_system_prompt(self, character_name: str, include_greeting: bool = True) -> str:
        """
        获取个性化的系统提示词
        
        Args:
            character_name: 人物名称
            include_greeting: 是否包含时间问候语
            
        Returns:
            系统提示词
        """
        character_config = self.load_character(character_name)
        
        # 获取基础提示词
        personality = character_config.get("personality", {})
        base_prompt = personality.get("base_prompt", "你是一个友善的AI助手。")
        
        # 替换人物名称
        character_display_name = character_config.get("name", character_name)
        system_prompt = base_prompt.format(name=character_display_name)
        
        # 添加时间问候语
        if include_greeting:
            greeting = self._get_time_greeting(character_config)
            if greeting:
                system_prompt += f"\n\n{greeting}"
        
        logger.info("personality", f"生成提示词: {character_name}")
        
        return system_prompt
    
    def list_available_characters(self) -> list[str]:
        """
        列出可用的人物配置
        
        Returns:
            人物名称列表
        """
        if not self.characters_dir.exists():
            return []
        
        characters = []
        for yaml_file in self.characters_dir.glob("*.yaml"):
            characters.append(yaml_file.stem)
        
        return sorted(characters)
    
    def get_character_info(self, character_name: str) -> Dict[str, str]:
        """
        获取人物基本信息
        
        Args:
            character_name: 人物名称
            
        Returns:
            包含人物信息的字典
        """
        config = self.load_character(character_name)
        
        return {
            "name": config.get("name", character_name),
            "description": config.get("description", "AI助手"),
            "traits": str(config.get("traits", {}))
        }
    
    def _get_time_greeting(self, character_config: Dict[str, Any]) -> Optional[str]:
        """
        根据当前时间获取问候语
        
        Args:
            character_config: 人物配置
            
        Returns:
            时间问候语，如果没有配置则返回None
        """
        greetings = character_config.get("greetings", {})
        if not greetings:
            return None
        
        now = datetime.now()
        hour = now.hour
        
        # 根据时间选择问候语
        if 5 <= hour < 11:
            time_key = "morning"
        elif 11 <= hour < 14:
            time_key = "noon"
        elif 14 <= hour < 18:
            time_key = "afternoon"
        elif 18 <= hour < 22:
            time_key = "evening"
        else:
            time_key = "night"
        
        return greetings.get(time_key)
    
    def _get_default_character(self) -> Dict[str, Any]:
        """
        获取默认人物配置
        
        Returns:
            默认配置字典
        """
        return {
            "name": "AI助手",
            "description": "友善的AI助手",
            "personality": {
                "base_prompt": "你是{name}，一个友善、专业的AI助手。请用中文回复，保持回答简洁明了，准确有用。"
            },
            "traits": {
                "humor_level": 5,
                "energy_level": 5,
                "caring_level": 7,
                "formality": 6
            }
        }


# 全局人物管理器实例
_personality_manager: Optional[PersonalityManager] = None


def get_personality_manager() -> PersonalityManager:
    """
    获取全局人物管理器实例（单例）
    
    Returns:
        PersonalityManager实例
    """
    global _personality_manager
    if _personality_manager is None:
        _personality_manager = PersonalityManager()
    return _personality_manager