"""
配置管理模块
"""
import yaml
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        self.conferences = self._load_yaml("conferences.yaml")
        self.settings = self._load_yaml("settings.yaml")
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"警告: 配置文件 {filepath} 不存在")
            return {}
        except yaml.YAMLError as e:
            print(f"错误: 解析YAML文件失败 {filepath}: {e}")
            return {}
    
    def get_all_conferences(self) -> Dict[str, Any]:
        """获取所有会议配置"""
        return self.conferences.get('conferences', {})
    
    def get_conference_config(self, conference_key: str) -> Dict[str, Any]:
        """获取特定会议的配置"""
        conferences = self.get_all_conferences()
        return conferences.get(conference_key, {})
    
    def get_setting(self, *keys: str, default: Any = None) -> Any:
        """
        获取设置值
        
        Args:
            *keys: 设置键路径
            default: 默认值
            
        Returns:
            设置值
        """
        value = self.settings
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
