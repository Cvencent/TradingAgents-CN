"""
工具配置数据模型
用于前后端API的数据交换
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class ToolParameter(BaseModel):
    """工具参数"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    default: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(..., description="是否必填")


class ToolConfig(BaseModel):
    """工具配置"""
    tool_id: str = Field(..., description="工具唯一标识")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category: str = Field(..., description="工具分类（market/social/news/fundamentals/general）")
    parameters: List[ToolParameter] = Field(default_factory=list, description="参数列表")
    remarks: str = Field(default="", description="备注信息")
    enabled: bool = Field(default=True, description="是否启用")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class ToolConfigListResponse(BaseModel):
    """工具配置列表响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List[ToolConfig] = Field(default_factory=list, description="工具配置列表")
    total: int = Field(default=0, description="总数")


class ToolConfigResponse(BaseModel):
    """工具配置响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[ToolConfig] = Field(None, description="工具配置")
