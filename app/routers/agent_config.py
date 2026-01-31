"""
Agent配置管理API路由
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.routers.auth_db import get_current_user
from app.core.database import get_mongo_db_sync
from tradingagents.utils.mongo_agent_config import MongoAgentConfig
from tradingagents.models.agent_config import AgentConfig, AgentConfigUpdate
from datetime import datetime
from app.utils.timezone import now_tz

from app.services.operation_log_service import log_operation
from app.models.operation_log import ActionType


router = APIRouter(prefix="/agent-config", tags=["Agent配置管理"])
logger = logging.getLogger("webapi")


class AgentConfigResponse(BaseModel):
    """Agent配置响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class AgentConfigListResponse(BaseModel):
    """Agent配置列表响应模型"""
    success: bool
    message: str
    data: List[Dict[str, Any]]
    total: int


class AgentConfigUpdateRequest(BaseModel):
    """Agent配置更新请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    system_message: Optional[str] = None
    prompt_template: Optional[str] = None
    tools: Optional[list] = None
    enabled: Optional[bool] = None


@router.get("", summary="获取所有Agent配置", response_model=AgentConfigListResponse)
async def get_all_agent_configs(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    获取所有Agent配置列表
    """
    try:
        mongo_agent_config = MongoAgentConfig(db)
        configs = mongo_agent_config.get_all_agent_configs()
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="获取所有Agent配置",
            details={"count": len(configs)},
            ip_address="",
            user_agent=""
        )
        
        return AgentConfigListResponse(
            success=True,
            message="获取Agent配置列表成功",
            data=configs,
            total=len(configs)
        )
    except Exception as e:
        logger.error(f"获取Agent配置列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Agent配置列表失败: {str(e)}"
        )


@router.get("/{agent_id}", summary="获取单个Agent配置", response_model=AgentConfigResponse)
async def get_agent_config(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    获取指定Agent的配置详情
    """
    try:
        mongo_agent_config = MongoAgentConfig(db)
        config = mongo_agent_config.get_agent_config(agent_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent配置不存在: {agent_id}"
            )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="获取Agent配置",
            details={"agent_id": agent_id},
            ip_address="",
            user_agent=""
        )
        
        return AgentConfigResponse(
            success=True,
            message="获取Agent配置成功",
            data=config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Agent配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Agent配置失败: {str(e)}"
        )


@router.post("/{agent_id}", summary="保存Agent配置", response_model=AgentConfigResponse)
async def save_agent_config(
    agent_id: str,
    config_data: AgentConfigUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    保存指定Agent的配置
    """
    try:
        # 获取现有配置
        mongo_agent_config = MongoAgentConfig(db)
        existing_config = mongo_agent_config.get_agent_config(agent_id)
        
        if not existing_config:
            # 创建新配置
            new_config = {
                "agent_id": agent_id,
                "name": config_data.name or f"Agent {agent_id}",
                "description": config_data.description or "",
                "system_message": config_data.system_message or "",
                "prompt_template": config_data.prompt_template or "",
                "tools": config_data.tools or [],
                "enabled": config_data.enabled if config_data.enabled is not None else True,
                "version": 1
            }
            success = mongo_agent_config.save_agent_config(new_config)
            action = "创建Agent配置"
        else:
            # 更新现有配置
            update_data = config_data.model_dump(exclude_unset=True)
            update_config = {**existing_config, **update_data}
            success = mongo_agent_config.save_agent_config(update_config)
            action = "更新Agent配置"
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存Agent配置失败"
            )
        
        # 获取更新后的配置
        updated_config = mongo_agent_config.get_agent_config(agent_id)
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action=action,
            details={"agent_id": agent_id, "changes": config_data.model_dump(exclude_unset=True)},
            ip_address="",
            user_agent=""
        )
        
        return AgentConfigResponse(
            success=True,
            message=f"{action}成功",
            data=updated_config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存Agent配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存Agent配置失败: {str(e)}"
        )


@router.delete("/{agent_id}", summary="删除Agent配置", response_model=AgentConfigResponse)
async def delete_agent_config(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    删除指定Agent的配置
    """
    try:
        mongo_agent_config = MongoAgentConfig(db)
        success = mongo_agent_config.delete_agent_config(agent_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent配置不存在: {agent_id}"
            )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="删除Agent配置",
            details={"agent_id": agent_id},
            ip_address="",
            user_agent=""
        )
        
        return AgentConfigResponse(
            success=True,
            message="删除Agent配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Agent配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Agent配置失败: {str(e)}"
        )


@router.post("/initialize", summary="初始化默认Agent配置", response_model=AgentConfigListResponse)
async def initialize_default_agent_configs(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    初始化默认Agent配置
    """
    try:
        mongo_agent_config = MongoAgentConfig(db)
        success = mongo_agent_config.initialize_default_configs()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="初始化默认Agent配置失败"
            )
        
        # 获取初始化后的配置
        configs = mongo_agent_config.get_all_agent_configs()
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="初始化默认Agent配置",
            details={"count": len(configs)},
            ip_address="",
            user_agent=""
        )
        
        return AgentConfigListResponse(
            success=True,
            message="初始化默认Agent配置成功",
            data=configs,
            total=len(configs)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化默认Agent配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化默认Agent配置失败: {str(e)}"
        )
