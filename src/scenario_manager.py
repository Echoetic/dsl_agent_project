#!/usr/bin/env python3
"""
场景管理器
负责加载和管理场景配置，提供场景的动态发现和访问
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ScenarioConfig:
    """场景配置"""
    id: str                              # 场景ID（如 hospital）
    name: str                            # 显示名称（如 医院智能客服）
    icon: str                            # 图标emoji
    description: str                     # 描述
    color: str                           # 主题色
    gradient: str                        # 渐变色
    features: List[str]                  # 功能列表
    script: str                          # DSL脚本文件名
    enabled: bool = True                 # 是否启用
    order: int = 0                       # 排序顺序
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'description': self.description,
            'color': self.color,
            'gradient': self.gradient,
            'features': self.features,
            'script': self.script,
            'enabled': self.enabled,
            'order': self.order
        }


@dataclass
class SiteConfig:
    """站点配置"""
    title: str = "DSL智能Agent系统"
    subtitle: str = "基于领域特定语言的多业务场景智能客服"
    description: str = ""
    footer_line1: str = ""
    footer_line2: str = ""
    
    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'description': self.description,
            'footer': {
                'line1': self.footer_line1,
                'line2': self.footer_line2
            }
        }


class ScenarioManager:
    """场景管理器"""
    
    def __init__(self, config_path: str = None, scripts_dir: str = None):
        """
        初始化场景管理器
        
        Args:
            config_path: 配置文件路径
            scripts_dir: DSL脚本目录
        """
        self.config_path = config_path
        self.scripts_dir = scripts_dir
        self.scenarios: Dict[str, ScenarioConfig] = {}
        self.site_config: SiteConfig = SiteConfig()
        
        # 自动检测路径
        if not config_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(base_dir, 'config', 'scenarios.json')
        
        if not scripts_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.scripts_dir = os.path.join(base_dir, 'scripts')
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载场景配置
                scenarios_data = config.get('scenarios', {})
                for scenario_id, data in scenarios_data.items():
                    self.scenarios[scenario_id] = ScenarioConfig(
                        id=scenario_id,
                        name=data.get('name', scenario_id),
                        icon=data.get('icon', '📋'),
                        description=data.get('description', ''),
                        color=data.get('color', '#666'),
                        gradient=data.get('gradient', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'),
                        features=data.get('features', []),
                        script=data.get('script', f'{scenario_id}.dsl'),
                        enabled=data.get('enabled', True),
                        order=data.get('order', 0)
                    )
                
                # 加载站点配置
                site_data = config.get('site', {})
                footer_data = site_data.get('footer', {})
                self.site_config = SiteConfig(
                    title=site_data.get('title', 'DSL智能Agent系统'),
                    subtitle=site_data.get('subtitle', ''),
                    description=site_data.get('description', ''),
                    footer_line1=footer_data.get('line1', ''),
                    footer_line2=footer_data.get('line2', '')
                )
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告: 无法加载配置文件 {self.config_path}: {e}")
                self._auto_discover_scenarios()
        else:
            # 配置文件不存在，自动发现场景
            self._auto_discover_scenarios()
    
    def _auto_discover_scenarios(self):
        """自动发现DSL脚本并创建场景配置"""
        if not os.path.exists(self.scripts_dir):
            return
        
        # 默认图标和颜色
        default_icons = ['📋', '📊', '📈', '📁', '🔧', '⚙️', '💼', '🎯']
        default_colors = ['#4CAF50', '#FF9800', '#9C27B0', '#2196F3', '#F44336', '#00BCD4']
        
        order = 0
        for filename in sorted(os.listdir(self.scripts_dir)):
            if filename.endswith('.dsl'):
                scenario_id = filename[:-4]  # 去掉.dsl后缀
                
                if scenario_id not in self.scenarios:
                    self.scenarios[scenario_id] = ScenarioConfig(
                        id=scenario_id,
                        name=scenario_id.replace('_', ' ').title(),
                        icon=default_icons[order % len(default_icons)],
                        description=f'{scenario_id} 场景',
                        color=default_colors[order % len(default_colors)],
                        gradient=f'linear-gradient(135deg, {default_colors[order % len(default_colors)]} 0%, #333 100%)',
                        features=[],
                        script=filename,
                        enabled=True,
                        order=order
                    )
                    order += 1
    
    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        """获取指定场景配置"""
        return self.scenarios.get(scenario_id)
    
    def get_enabled_scenarios(self) -> List[ScenarioConfig]:
        """获取所有启用的场景，按order排序"""
        enabled = [s for s in self.scenarios.values() if s.enabled]
        return sorted(enabled, key=lambda s: s.order)
    
    def get_all_scenarios(self) -> List[ScenarioConfig]:
        """获取所有场景"""
        return sorted(self.scenarios.values(), key=lambda s: s.order)
    
    def get_script_path(self, scenario_id: str) -> Optional[str]:
        """获取场景的DSL脚本路径"""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            return os.path.join(self.scripts_dir, scenario.script)
        return None
    
    def scenario_exists(self, scenario_id: str) -> bool:
        """检查场景是否存在且已启用"""
        scenario = self.get_scenario(scenario_id)
        return scenario is not None and scenario.enabled
    
    def get_scenarios_for_api(self) -> List[dict]:
        """获取用于API返回的场景列表"""
        return [s.to_dict() for s in self.get_enabled_scenarios()]
    
    def get_site_config(self) -> SiteConfig:
        """获取站点配置"""
        return self.site_config
    
    def reload(self):
        """重新加载配置"""
        self.scenarios.clear()
        self._load_config()
    
    def add_scenario(self, scenario: ScenarioConfig) -> bool:
        """添加新场景"""
        if scenario.id in self.scenarios:
            return False
        self.scenarios[scenario.id] = scenario
        return True
    
    def update_scenario(self, scenario_id: str, **kwargs) -> bool:
        """更新场景配置"""
        if scenario_id not in self.scenarios:
            return False
        
        scenario = self.scenarios[scenario_id]
        for key, value in kwargs.items():
            if hasattr(scenario, key):
                setattr(scenario, key, value)
        return True
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            config = {
                'scenarios': {
                    s.id: {
                        'name': s.name,
                        'icon': s.icon,
                        'description': s.description,
                        'color': s.color,
                        'gradient': s.gradient,
                        'features': s.features,
                        'script': s.script,
                        'enabled': s.enabled,
                        'order': s.order
                    }
                    for s in self.scenarios.values()
                },
                'site': self.site_config.to_dict()
            }
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存配置失败: {e}")
            return False


# 全局场景管理器实例
_scenario_manager: Optional[ScenarioManager] = None


def get_scenario_manager() -> ScenarioManager:
    """获取全局场景管理器实例"""
    global _scenario_manager
    if _scenario_manager is None:
        _scenario_manager = ScenarioManager()
    return _scenario_manager


def init_scenario_manager(config_path: str = None, scripts_dir: str = None) -> ScenarioManager:
    """初始化全局场景管理器"""
    global _scenario_manager
    _scenario_manager = ScenarioManager(config_path, scripts_dir)
    return _scenario_manager