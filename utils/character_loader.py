"""
角色加载器模块
负责从本地TOML文件加载和解析角色数据
"""
import tomli
from typing import Dict, Any, List
from pathlib import Path


class CharacterLoader:
    """角色加载器"""
    
    def __init__(self, characters_dir: str = None):
        """
        初始化角色加载器
        
        Args:
            characters_dir: 角色配置文件目录路径
        """
        if characters_dir is None:
            # 默认使用项目根目录下的characters文件夹
            self.characters_dir = Path(__file__).parent.parent / "characters"
        else:
            self.characters_dir = Path(characters_dir)
            
        # 确保目录存在
        if not self.characters_dir.exists():
            raise FileNotFoundError(f"角色配置目录不存在: {self.characters_dir}")
        
        # 加载所有角色数据
        self._characters = self._load_all_characters()
    
    def _load_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """
        从本地文件加载所有角色配置
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有角色配置数据，以角色名为键
        """
        characters = {}
        
        # 查找所有.toml文件
        for toml_file in self.characters_dir.glob("*.toml"):
            character_name = toml_file.stem  # 获取不带扩展名的文件名
            try:
                with open(toml_file, 'rb') as f:
                    character_data = tomli.load(f)
                    # 填充角色名称（如果未在文件中指定）
                    if 'name' not in character_data:
                        character_data['name'] = character_name
                    characters[character_name] = character_data
            except Exception as e:
                # 记录错误但继续加载其他角色
                print(f"警告: 无法加载角色 {character_name}: {str(e)}")
                
        return characters
    
    def get_character(self, character_name: str) -> Dict[str, Any]:
        """
        获取指定角色的配置
        
        Args:
            character_name: 角色名称
            
        Returns:
            Dict[str, Any]: 角色配置数据
        """
        return self._characters.get(character_name, {})
    
    def get_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有角色配置
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有角色配置数据
        """
        return self._characters.copy()
    
    def get_available_characters(self) -> List[str]:
        """
        获取所有可用角色名称
        
        Returns:
            List[str]: 可用角色名称列表
        """
        return list(self._characters.keys())
    
    def format_system_prompt(self, character_name: str) -> str:
        """
        格式化角色的系统提示词
        
        Args:
            character_name: 角色名称
            
        Returns:
            str: 格式化后的系统提示词
        """
        char_data = self._characters.get(character_name, {})
        personality = char_data.get("personality", {})
        base_prompt = personality.get("base_prompt", "")
        
        # 如果有base_prompt模板，进行格式化
        if base_prompt and "{name}" in base_prompt:
            return base_prompt.format(name=char_data.get("name", ""))
        
        return base_prompt