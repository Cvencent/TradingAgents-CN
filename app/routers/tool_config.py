"""
工具配置管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from app.models.tool_config import (
    ToolConfig,
    ToolConfigListResponse,
    ToolConfigResponse
)
from app.core.database import get_mongo_db_sync
from app.routers.auth_db import get_current_user
from app.services.operation_log_service import log_operation
from app.models.operation_log import ActionType
from tradingagents.utils.mongo_tool_config import MongoToolConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["工具管理"])


@router.get("", summary="获取所有工具列表", response_model=ToolConfigListResponse)
async def get_all_tools(
    category: Optional[str] = None,
    enabled_only: bool = False,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    获取所有工具列表
    
    Query Parameters:
        category: 工具分类（market/social/news/fundamentals/general）
        enabled_only: 是否只返回启用的工具
    """
    try:
        mongo_tool_config = MongoToolConfig(db)
        
        if category:
            configs = mongo_tool_config.get_all_tools_by_category(category)
        else:
            configs = mongo_tool_config.get_all_tool_configs()
        
        if enabled_only:
            configs = [c for c in configs if c.get("enabled", True)]
        
        tool_configs = []
        for config in configs:
            tool_config = ToolConfig(
                tool_id=config.get("tool_id", ""),
                name=config.get("name", ""),
                description=config.get("description", ""),
                category=config.get("category", "general"),
                parameters=config.get("parameters", []),
                remarks=config.get("remarks", ""),
                enabled=config.get("enabled", True),
                created_at=config.get("created_at"),
                updated_at=config.get("updated_at")
            )
            tool_configs.append(tool_config)
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="获取工具列表",
            details={"category": category, "enabled_only": enabled_only},
            ip_address="",
            user_agent=""
        )
        
        return ToolConfigListResponse(
            success=True,
            message="获取工具列表成功",
            data=tool_configs,
            total=len(tool_configs)
        )
    except Exception as e:
        logger.error(f"❌ 获取工具列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


@router.get("/{tool_id}", summary="获取工具详情", response_model=ToolConfigResponse)
async def get_tool_detail(
    tool_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    获取工具详情
    """
    try:
        mongo_tool_config = MongoToolConfig(db)
        config = mongo_tool_config.get_tool_config(tool_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {tool_id}"
            )
        
        tool_config = ToolConfig(
            tool_id=config.get("tool_id", ""),
            name=config.get("name", ""),
            description=config.get("description", ""),
            category=config.get("category", "general"),
            parameters=config.get("parameters", []),
            remarks=config.get("remarks", ""),
            enabled=config.get("enabled", True),
            created_at=config.get("created_at"),
            updated_at=config.get("updated_at")
        )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="获取工具详情",
            details={"tool_id": tool_id},
            ip_address="",
            user_agent=""
        )
        
        return ToolConfigResponse(
            success=True,
            message="获取工具详情成功",
            data=tool_config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取工具详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具详情失败: {str(e)}"
        )


@router.put("/{tool_id}", summary="更新工具配置", response_model=ToolConfigResponse)
async def update_tool_config(
    tool_id: str,
    remarks: Optional[str] = None,
    enabled: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    更新工具配置（备注、启用状态）
    """
    try:
        mongo_tool_config = MongoToolConfig(db)
        existing_config = mongo_tool_config.get_tool_config(tool_id)
        
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {tool_id}"
            )
        
        update_data = {"tool_id": tool_id}
        if remarks is not None:
            update_data["remarks"] = remarks
        if enabled is not None:
            update_data["enabled"] = enabled
        
        success = mongo_tool_config.save_tool_config(update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新工具配置失败"
            )
        
        updated_config = mongo_tool_config.get_tool_config(tool_id)
        tool_config = ToolConfig(
            tool_id=updated_config.get("tool_id", ""),
            name=updated_config.get("name", ""),
            description=updated_config.get("description", ""),
            category=updated_config.get("category", "general"),
            parameters=updated_config.get("parameters", []),
            remarks=updated_config.get("remarks", ""),
            enabled=updated_config.get("enabled", True),
            created_at=updated_config.get("created_at"),
            updated_at=updated_config.get("updated_at")
        )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="更新工具配置",
            details={"tool_id": tool_id, "update_data": update_data},
            ip_address="",
            user_agent=""
        )
        
        return ToolConfigResponse(
            success=True,
            message="更新工具配置成功",
            data=tool_config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 更新工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工具配置失败: {str(e)}"
        )


@router.post("/initialize", summary="初始化默认工具配置", response_model=ToolConfigListResponse)
async def initialize_default_tools(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    初始化默认工具配置（从工具注册器同步）
    """
    try:
        from tradingagents.agents.utils.tool_registry import get_tool_registry
        
        mongo_tool_config = MongoToolConfig(db)
        success = mongo_tool_config.initialize_default_tools(get_tool_registry())
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="初始化默认工具配置失败"
            )
        
        configs = mongo_tool_config.get_all_tool_configs()
        tool_configs = []
        for config in configs:
            tool_config = ToolConfig(
                tool_id=config.get("tool_id", ""),
                name=config.get("name", ""),
                description=config.get("description", ""),
                category=config.get("category", "general"),
                parameters=config.get("parameters", []),
                remarks=config.get("remarks", ""),
                enabled=config.get("enabled", True),
                created_at=config.get("created_at"),
                updated_at=config.get("updated_at")
            )
            tool_configs.append(tool_config)
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="初始化默认工具配置",
            details={"total": len(tool_configs)},
            ip_address="",
            user_agent=""
        )
        
        return ToolConfigListResponse(
            success=True,
            message="初始化默认工具配置成功",
            data=tool_configs,
            total=len(tool_configs)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 初始化默认工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化默认工具配置失败: {str(e)}"
        )
