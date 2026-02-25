"""
角色模型配置数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from app.utils.timezone import now_tz
from .user import PyObjectId


class ModelConfigRef(BaseModel):
    """模型配置引用"""
    provider: str = Field(..., description="模型厂家")
    model_name: str = Field(..., description="模型名称")
    temperature: Optional[float] = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(default=4000, description="最大token数")
    timeout: Optional[int] = Field(default=180, description="超时时间(秒)")
    
    model_config = ConfigDict(populate_by_name=True)


class RoleModelConfigRef(BaseModel):
    """角色模型配置引用（用于预设）"""
    provider: str = Field(..., description="模型厂家")
    model_name: str = Field(..., description="模型名称")
    temperature: Optional[float] = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(default=4000, description="最大token数")
    custom_prompt: Optional[str] = Field(None, description="角色特定的系统提示词覆盖")
    
    model_config = ConfigDict(populate_by_name=True)


class RoleModelConfig(BaseModel):
    """角色模型配置"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # 角色标识
    role_id: str = Field(..., description="角色ID，如：market, bull, investment_manager")
    role_type: str = Field(..., description="角色类型：analyst/debater/decision_maker")
    role_name: str = Field(..., description="角色显示名称")
    
    # 模型配置
    provider: str = Field(..., description="模型厂家")
    model_name: str = Field(..., description="模型名称")
    model_display_name: Optional[str] = Field(None, description="模型显示名称")
    
    # 模型参数
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4000, description="最大token数")
    timeout: int = Field(default=180, description="超时时间(秒)")
    
    # 启用状态
    is_enabled: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否为该类型角色的默认配置")
    
    # 元数据
    description: Optional[str] = Field(None, description="配置描述")
    created_at: datetime = Field(default_factory=now_tz)
    updated_at: datetime = Field(default_factory=now_tz)
    created_by: Optional[str] = Field(None, description="创建者")
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class ModelSelectionPreset(BaseModel):
    """模型选择预设方案"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    name: str = Field(..., description="预设名称")
    description: Optional[str] = Field(None, description="预设描述")
    
    # 预设类型：system（系统预设）/ user（用户自定义）
    preset_type: str = Field(default="user", description="预设类型")
    
    # 角色配置映射
    role_configs: Dict[str, RoleModelConfigRef] = Field(default_factory=dict, description="角色配置映射")
    # 格式：{"market": {"provider": "openai", "model_name": "gpt-4"}, ...}
    
    # 默认配置（当角色没有特定配置时使用）
    default_provider: str = Field(..., description="默认厂家")
    default_model: str = Field(..., description="默认模型")
    
    is_active: bool = Field(default=True, description="是否激活")
    is_system: bool = Field(default=False, description="是否为系统预设")
    
    created_at: datetime = Field(default_factory=now_tz)
    updated_at: datetime = Field(default_factory=now_tz)
    created_by: Optional[str] = Field(None, description="创建者")
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class AnalysisModelConfig(BaseModel):
    """分析任务模型配置（运行时配置）"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # 关联的分析任务或用户
    task_id: Optional[str] = Field(None, description="任务ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    
    # 使用的预设
    preset_id: Optional[str] = Field(None, description="预设ID")
    
    # 实际使用的模型配置（展开后的完整配置）
    analyst_models: Dict[str, ModelConfigRef] = Field(default_factory=dict, description="分析师模型配置")
    debater_models: Dict[str, ModelConfigRef] = Field(default_factory=dict, description="辩论者模型配置")
    decision_models: Dict[str, ModelConfigRef] = Field(default_factory=dict, description="决策者模型配置")
    
    # 默认模型（当特定角色没有配置时使用）
    default_model: Optional[ModelConfigRef] = Field(None, description="默认模型配置")
    
    created_at: datetime = Field(default_factory=now_tz)
    updated_at: datetime = Field(default_factory=now_tz)
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


# 请求/响应模型

class RoleModelConfigUpdate(BaseModel):
    """角色模型配置更新请求"""
    provider: str = Field(..., description="模型厂家")
    model_name: str = Field(..., description="模型名称")
    model_display_name: Optional[str] = Field(None, description="模型显示名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000)
    timeout: int = Field(default=180)
    is_enabled: bool = Field(default=True)
    description: Optional[str] = Field(None)


class RoleModelConfigResponse(BaseModel):
    """角色模型配置响应"""
    id: str
    role_id: str
    role_type: str
    role_name: str
    provider: str
    model_name: str
    model_display_name: Optional[str] = None
    temperature: float
    max_tokens: int
    timeout: int
    is_enabled: bool
    is_default: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BatchRoleModelConfigUpdate(BaseModel):
    """批量角色模型配置更新请求"""
    configs: List[RoleModelConfigUpdate] = Field(..., description="配置列表")


class ModelSelectionPresetCreate(BaseModel):
    """模型选择预设创建请求"""
    name: str = Field(..., description="预设名称")
    description: Optional[str] = Field(None)
    role_configs: Dict[str, RoleModelConfigRef] = Field(default_factory=dict)
    default_provider: str = Field(...)
    default_model: str = Field(...)


class ModelSelectionPresetUpdate(BaseModel):
    """模型选择预设更新请求"""
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    role_configs: Optional[Dict[str, RoleModelConfigRef]] = Field(None)
    default_provider: Optional[str] = Field(None)
    default_model: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class ModelSelectionPresetResponse(BaseModel):
    """模型选择预设响应"""
    id: str
    name: str
    description: Optional[str] = None
    preset_type: str
    role_configs: Dict[str, RoleModelConfigRef]
    default_provider: str
    default_model: str
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime


class ActiveModelConfigResponse(BaseModel):
    """当前生效的模型配置响应"""
    preset_id: Optional[str] = None
    preset_name: Optional[str] = None
    configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    default_model: Optional[ModelConfigRef] = None


class ApplyPresetResponse(BaseModel):
    """应用预设响应"""
    success: bool
    message: str
    applied_configs: int
