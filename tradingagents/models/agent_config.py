"""Agent配置数据模型"""

from typing import Dict, Optional, Any
from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Agent配置模型"""
    # 基本信息
    agent_id: str  # 分析师唯一标识，如：fundamentals, market, news, china_market, social_media
    name: str  # 分析师名称，如：基本面分析师
    description: str  # 分析师描述
    
    # 提示词配置
    system_message: str  # 系统消息
    prompt_template: str  # 提示模板
    
    # 工具配置
    tools: list  # 工具列表
    
    # 其他配置
    enabled: bool = True  # 是否启用
    version: int = 1  # 版本号
    created_at: Optional[str] = None  # 创建时间
    updated_at: Optional[str] = None  # 更新时间
    
    class Config:
        extra = "allow"


class AgentConfigUpdate(BaseModel):
    """Agent配置更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    system_message: Optional[str] = None
    prompt_template: Optional[str] = None
    tools: Optional[list] = None
    enabled: Optional[bool] = None
    
    class Config:
        extra = "allow"
