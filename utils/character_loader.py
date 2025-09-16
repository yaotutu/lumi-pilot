"""
角色加载器模块
负责从单个TOML文件加载和解析角色数据
"""
import tomli
from typing import Dict, Any, Optional
from pathlib import Path


class CharacterLoader:
    """角色加载器"""
    
    def __init__(self, character_file: str = None):
        """
        初始化角色加载器
        
        Args:
            character_file: 角色配置文件路径，默认为characters/lumi.toml
        """
        if character_file is None:
            # 默认使用项目根目录下的characters/lumi.toml
            self.character_file = Path(__file__).parent.parent / "characters" / "lumi.toml"
        else:
            self.character_file = Path(character_file)
            
        # 确保文件存在
        if not self.character_file.exists():
            raise FileNotFoundError(f"角色配置文件不存在: {self.character_file}")
        
        # 加载角色数据
        self._character_data = self._load_character()
    
    def _load_character(self) -> Dict[str, Any]:
        """
        从文件加载角色配置
        
        Returns:
            Dict[str, Any]: 角色配置数据
        """
        try:
            with open(self.character_file, 'rb') as f:
                character_data = tomli.load(f)
                # 填充角色名称（如果未在文件中指定）
                if 'name' not in character_data:
                    character_data['name'] = self.character_file.stem
                return character_data
        except Exception as e:
            raise Exception(f"解析角色配置文件失败 {self.character_file}: {str(e)}")
    
    def get_character_data(self) -> Dict[str, Any]:
        """
        获取角色配置数据
        
        Returns:
            Dict[str, Any]: 角色配置数据
        """
        return self._character_data
    
    def get_system_prompt(self) -> str:
        """
        获取格式化后的系统提示词
        
        Returns:
            str: 格式化后的系统提示词
        """
        personality = self._character_data.get("personality", {})
        base_prompt = personality.get("base_prompt", "")
        
        # 如果有base_prompt模板，进行格式化
        if base_prompt and "{name}" in base_prompt:
            return base_prompt.format(name=self._character_data.get("name", ""))
        
        return base_prompt
    
    def get_character_name(self) -> str:
        """
        获取角色名称
        
        Returns:
            str: 角色名称
        """
        return self._character_data.get("name", self.character_file.stem)