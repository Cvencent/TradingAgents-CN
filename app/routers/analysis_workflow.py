"""
分析流程配置 API 路由
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.routers.auth_db import get_current_user
from app.core.database import get_mongo_db_sync
from app.services.analysis_workflow_service import MongoAnalysisWorkflowConfig
from app.models.analysis_workflow import (
    AnalysisWorkflowConfig,
    WorkflowConfigCreate,
    WorkflowConfigUpdate,
    WorkflowConfigResponse,
    WorkflowConfigListResponse
)
from app.services.operation_log_service import log_operation
from app.models.operation_log import ActionType


router = APIRouter(prefix="/analysis-workflow", tags=["分析流程配置"])
logger = logging.getLogger("webapi")


def get_workflow_service(db):
    """获取分析流程配置服务实例"""
    return MongoAnalysisWorkflowConfig(db)


@router.get("/workflows", summary="获取所有流程配置", response_model=WorkflowConfigListResponse)
async def get_all_workflow_configs(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    获取用户的所有流程配置列表
    """
    try:
        workflow_service = get_workflow_service(db)
        user_id = str(current_user.get("user_id", ""))
        
        configs = workflow_service.get_all_workflow_configs(user_id)
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="获取分析流程配置列表",
            details={"count": len(configs)},
            ip_address="",
            user_agent=""
        )
        
        return WorkflowConfigListResponse(
            success=True,
            message="获取流程配置列表成功",
            data=configs,
            total=len(configs)
        )
    except Exception as e:
        logger.error(f"获取流程配置列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取流程配置列表失败: {str(e)}"
        )


@router.get("/workflows/{config_id}", summary="获取单个流程配置", response_model=WorkflowConfigResponse)
async def get_workflow_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    获取指定流程配置详情
    """
    try:
        workflow_service = get_workflow_service(db)
        user_id = str(current_user.get("user_id", ""))
        
        config = workflow_service.get_workflow_config(config_id, user_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"流程配置不存在: {config_id}"
            )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="获取流程配置",
            details={"config_id": config_id},
            ip_address="",
            user_agent=""
        )
        
        return WorkflowConfigResponse(
            success=True,
            message="获取流程配置成功",
            data=config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取流程配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取流程配置失败: {str(e)}"
        )


@router.post("/workflows", summary="创建流程配置", response_model=WorkflowConfigResponse)
async def create_workflow_config(
    config_data: WorkflowConfigCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    创建新的流程配置
    """
    try:
        workflow_service = get_workflow_service(db)
        user_id = str(current_user.get("user_id", ""))
        
        config_dict = config_data.model_dump()
        success = workflow_service.save_workflow_config(config_dict, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建流程配置失败"
            )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="创建流程配置",
            details={"name": config_data.name},
            ip_address="",
            user_agent=""
        )
        
        return WorkflowConfigResponse(
            success=True,
            message="创建流程配置成功",
            data=config_dict
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建流程配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建流程配置失败: {str(e)}"
        )


@router.put("/workflows/{config_id}", summary="更新流程配置", response_model=WorkflowConfigResponse)
async def update_workflow_config(
    config_id: str,
    config_data: WorkflowConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    更新流程配置
    """
    try:
        workflow_service = get_workflow_service(db)
        user_id = str(current_user.get("user_id", ""))
        
        existing_config = workflow_service.get_workflow_config(config_id, user_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"流程配置不存在: {config_id}"
            )
        
        # 检查是否是系统预设
        if existing_config.get("is_system", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="系统预设配置不允许编辑，请创建新的自定义配置"
            )
        
        update_dict = config_data.model_dump(exclude_unset=True)
        update_dict["_id"] = config_id
        success = workflow_service.save_workflow_config(update_dict, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新流程配置失败"
            )
        
        updated_config = workflow_service.get_workflow_config(config_id, user_id)
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="更新流程配置",
            details={"config_id": config_id, "changes": update_dict},
            ip_address="",
            user_agent=""
        )
        
        return WorkflowConfigResponse(
            success=True,
            message="更新流程配置成功",
            data=updated_config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新流程配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新流程配置失败: {str(e)}"
        )


@router.delete("/workflows/{config_id}", summary="删除流程配置", response_model=WorkflowConfigResponse)
async def delete_workflow_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    删除流程配置
    """
    try:
        workflow_service = get_workflow_service(db)
        user_id = str(current_user.get("user_id", ""))
        
        success = workflow_service.delete_workflow_config(config_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"流程配置不存在或无权删除: {config_id}"
            )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="删除流程配置",
            details={"config_id": config_id},
            ip_address="",
            user_agent=""
        )
        
        return WorkflowConfigResponse(
            success=True,
            message="删除流程配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除流程配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除流程配置失败: {str(e)}"
        )


@router.post("/workflows/{config_id}/set-default", summary="设置为默认配置", response_model=WorkflowConfigResponse)
async def set_default_workflow_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    设置指定配置为默认配置
    """
    try:
        workflow_service = get_workflow_service(db)
        user_id = str(current_user.get("user_id", ""))
        
        success = workflow_service.set_default_config(user_id, config_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"流程配置不存在: {config_id}"
            )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="设置默认流程配置",
            details={"config_id": config_id},
            ip_address="",
            user_agent=""
        )
        
        return WorkflowConfigResponse(
            success=True,
            message="设置默认配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置默认配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置默认配置失败: {str(e)}"
        )


@router.get("/workflows/default", summary="获取默认配置", response_model=WorkflowConfigResponse)
async def get_default_workflow_config(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    获取用户的默认流程配置
    """
    try:
        workflow_service = get_workflow_service(db)
        user_id = str(current_user.get("user_id", ""))
        
        config = workflow_service.get_default_config(user_id)
        
        if not config:
            return WorkflowConfigResponse(
                success=True,
                message="未设置默认配置",
                data=None
            )
        
        return WorkflowConfigResponse(
            success=True,
            message="获取默认配置成功",
            data=config
        )
    except Exception as e:
        logger.error(f"获取默认配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取默认配置失败: {str(e)}"
        )


@router.post("/workflows/initialize-presets", summary="初始化系统预设", response_model=WorkflowConfigResponse)
async def initialize_system_presets(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    初始化系统预设流程配置
    """
    try:
        workflow_service = get_workflow_service(db)
        success = workflow_service.initialize_system_presets()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="初始化系统预设失败"
            )
        
        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="初始化系统预设",
            details={},
            ip_address="",
            user_agent=""
        )
        
        return WorkflowConfigResponse(
            success=True,
            message="初始化系统预设成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化系统预设失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化系统预设失败: {str(e)}"
        )
