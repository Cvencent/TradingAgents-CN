"""
工具注册器
用于自动注册和管理所有工具
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import inspect


@dataclass
class ToolInfo:
    """工具信息"""
    tool_id: str                          # 工具唯一标识
    name: str                              # 工具名称
    description: str                       # 工具描述
    category: str                          # 工具分类（market/social/news/fundamentals/general）
    func: Callable                        # 工具函数
    parameters: List[Dict[str, Any]] = field(default_factory=list)  # 参数列表
    remarks: str = ""                     # 备注信息
    enabled: bool = True                   # 是否启用
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ToolRegistry:
    """工具注册器（单例模式）"""
    
    _instance = None
    _tools: Dict[str, ToolInfo] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_tool(
        cls,
        tool_func: Callable,
        category: str = "general",
        description: str = "",
        remarks: str = ""
    ) -> ToolInfo:
        """
        注册工具
        
        Args:
            tool_func: 工具函数
            category: 工具分类
            description: 工具描述
            remarks: 备注信息
            
        Returns:
            工具信息对象
        """
        tool_id = tool_func.__name__
        
        # 提取参数信息
        parameters = cls._extract_parameters(tool_func)
        
        # 创建工具信息
        tool_info = ToolInfo(
            tool_id=tool_id,
            name=tool_func.__name__,
            description=description or tool_func.__doc__ or "",
            category=category,
            func=tool_func,
            parameters=parameters,
            remarks=remarks,
            enabled=True
        )
        
        # 注册到全局注册表
        cls._tools[tool_id] = tool_info
        
        return tool_info
    
    @classmethod
    def _extract_parameters(cls, func: Callable) -> List[Dict[str, Any]]:
        """提取函数参数信息"""
        parameters = []
        sig = inspect.signature(func)
        
        for name, param in sig.parameters.items():
            param_info = {
                "name": name,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "default": param.default if param.default != inspect.Parameter.empty else None,
                "required": param.default == inspect.Parameter.empty
            }
            parameters.append(param_info)
        
        return parameters
    
    @classmethod
    def get_tool(cls, tool_name: str) -> Optional[ToolInfo]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具信息对象，如果不存在则返回 None
        """
        return cls._tools.get(tool_name)
    
    @classmethod
    def get_all_tools(cls) -> List[ToolInfo]:
        """
        获取所有工具
        
        Returns:
            所有工具信息列表
        """
        return list(cls._tools.values())
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> List[ToolInfo]:
        """
        获取指定分类的工具
        
        Args:
            category: 工具分类
            
        Returns:
            指定分类的工具列表
        """
        return [tool for tool in cls._tools.values() if tool.category == category]
    
    @classmethod
    def get_enabled_tools(cls) -> List[ToolInfo]:
        """
        获取所有启用的工具
        
        Returns:
            所有启用的工具列表
        """
        return [tool for tool in cls._tools.values() if tool.enabled]
    
    @classmethod
    def update_tool_remarks(cls, tool_name: str, remarks: str) -> bool:
        """
        更新工具备注
        
        Args:
            tool_name: 工具名称
            remarks: 备注信息
            
        Returns:
            是否更新成功
        """
        tool = cls._tools.get(tool_name)
        if tool:
            tool.remarks = remarks
            tool.updated_at = datetime.now().isoformat()
            return True
        return False
    
    @classmethod
    def enable_tool(cls, tool_name: str, enabled: bool = True) -> bool:
        """
        启用或禁用工具
        
        Args:
            tool_name: 工具名称
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        tool = cls._tools.get(tool_name)
        if tool:
            tool.enabled = enabled
            tool.updated_at = datetime.now().isoformat()
            return True
        return False
    
    @classmethod
    def clear_registry(cls):
        """清空注册表（主要用于测试）"""
        cls._tools.clear()


def register_tool(category: str = "general", description: str = "", remarks: str = ""):
    """
    工具注册装饰器
    
    Args:
        category: 工具分类
        description: 工具描述
        remarks: 备注信息
        
    Example:
        @register_tool(category="market", description="获取股票市场数据")
        def get_stock_market_data(ticker: str, date: str) -> str:
            pass
    """
    def decorator(func: Callable):
        ToolRegistry.register_tool(
            tool_func=func,
            category=category,
            description=description,
            remarks=remarks
        )
        return func
    return decorator


def get_tool_registry() -> ToolRegistry:
    """
    获取工具注册器实例
    
    Returns:
        工具注册器单例实例
    """
    return ToolRegistry()
