"""
分析流程配置相关数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from .user import PyObjectId
from app.utils.timezone import now_tz


class AnalysisWorkflowConfig(BaseModel):
    """分析流程配置模型"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="用户ID")
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    
    # 关联分析级别（1-5级）
    analysis_level: int = Field(default=5, ge=1, le=5, description="关联的分析级别（1-5级）")
    
    # 辩论配置
    debate_rounds: int = Field(default=1, ge=1, le=3, description="多空辩论轮次（1-3轮）")
    debate_timeout: int = Field(default=300, ge=60, le=600, description="每轮超时时间（秒）")
    
    # 风险评估配置
    risk_discussion_rounds: int = Field(default=1, ge=1, le=3, description="风险讨论轮次（1-3轮）")
    risk_timeout: int = Field(default=120, ge=30, le=300, description="风险讨论超时时间（秒）")
    
    # 其他配置
    enable_sentiment: bool = Field(default=True, description="是否启用情绪分析")
    enable_risk_assessment: bool = Field(default=True, description="是否启用风险评估")
    max_retries: int = Field(default=3, ge=1, le=5, description="最大重试次数")
    
    # 模型配置
    quick_analysis_model: Optional[str] = Field(None, description="快速分析模型")
    deep_analysis_model: Optional[str] = Field(None, description="深度分析模型")
    
    # 元数据
    is_default: bool = Field(default=False, description="是否为默认配置")
    is_system: bool = Field(default=False, description="是否为系统预设配置")
    created_at: datetime = Field(default_factory=now_tz, description="创建时间")
    updated_at: datetime = Field(default_factory=now_tz, description="更新时间")
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class WorkflowConfigCreate(BaseModel):
    """创建流程配置请求模型"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    analysis_level: int = Field(default=5, ge=1, le=5, description="关联的分析级别（1-5级）")
    debate_rounds: int = Field(default=1, ge=1, le=3)
    debate_timeout: int = Field(default=300, ge=60, le=600)
    risk_discussion_rounds: int = Field(default=1, ge=1, le=3)
    risk_timeout: int = Field(default=120, ge=30, le=300)
    enable_sentiment: bool = Field(default=True)
    enable_risk_assessment: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=1, le=5)
    quick_analysis_model: Optional[str] = None
    deep_analysis_model: Optional[str] = None


class WorkflowConfigUpdate(BaseModel):
    """更新流程配置请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    analysis_level: Optional[int] = Field(None, ge=1, le=5)
    debate_rounds: Optional[int] = Field(None, ge=1, le=3)
    debate_timeout: Optional[int] = Field(None, ge=60, le=600)
    risk_discussion_rounds: Optional[int] = Field(None, ge=1, le=3)
    risk_timeout: Optional[int] = Field(None, ge=30, le=300)
    enable_sentiment: Optional[bool] = None
    enable_risk_assessment: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=1, le=5)
    quick_analysis_model: Optional[str] = None
    deep_analysis_model: Optional[str] = None


class WorkflowConfigResponse(BaseModel):
    """流程配置响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class WorkflowConfigListResponse(BaseModel):
    """流程配置列表响应模型"""
    success: bool
    message: str
    data: List[Dict[str, Any]]
    total: int
