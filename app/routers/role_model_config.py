"""
角色模型配置路由
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.routers.auth_db import ApiResponse
from app.models.role_model_config import (
    RoleModelConfigUpdate,
    RoleModelConfigResponse,
    ModelSelectionPresetCreate,
    ModelSelectionPresetUpdate,
    ModelSelectionPresetResponse,
    ActiveModelConfigResponse,
    ApplyPresetResponse,
)
from app.services.role_model_config_service import RoleModelConfigService

router = APIRouter(prefix="/api/config", tags=["角色模型配置"])

# 初始化 logger
logger = logging.getLogger(__name__)


def get_service() -> RoleModelConfigService:
    """获取服务实例"""
    return RoleModelConfigService()


# ==================== 角色配置 API ====================

@router.get("/role-models")
async def get_all_role_configs(
    service: RoleModelConfigService = Depends(get_service)
):
    """
    获取所有角色配置

    返回按角色类型分组的配置列表（分析师、辩论者、决策者）
    """
    try:
        print("[DEBUG] 开始获取角色配置...")
        configs = await service.get_all_role_configs()
        print(f"[DEBUG] 获取角色配置成功: {len(configs)} 个类型")
        return {"success": True, "data": configs, "message": "ok"}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] 获取角色配置失败!")
        print(f"[ERROR] 异常类型: {type(e)}")
        print(f"[ERROR] 异常消息: {repr(str(e))}")
        print(f"[ERROR] 异常详情:\n{error_detail}")
        return {"success": False, "data": {"analysts": [], "debaters": [], "decision_makers": []}, "message": f"获取角色配置失败: {str(e)}"}


@router.get("/role-models/{role_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_role_config(
    role_id: str,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    获取单个角色配置
    
    Args:
        role_id: 角色ID (如: market, bull, investment_manager)
    """
    try:
        config = await service.get_role_config(role_id)
        if not config:
            return ApiResponse.error(message="角色配置不存在")
        return ApiResponse.success(data=config.model_dump())
    except Exception as e:
        return ApiResponse.error(message=f"获取角色配置失败: {str(e)}")


@router.put("/role-models/{role_id}", response_model=ApiResponse[Dict[str, Any]])
async def update_role_config(
    role_id: str,
    update: RoleModelConfigUpdate,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    更新角色模型配置
    
    Args:
        role_id: 角色ID
        update: 配置更新数据
    """
    try:
        config = await service.update_role_config(role_id, update)
        return ApiResponse.success(
            message="更新成功",
            data=config.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return ApiResponse.error(message=f"更新角色配置失败: {str(e)}")


@router.put("/role-models/batch", response_model=ApiResponse[Dict[str, Any]])
async def batch_update_role_configs(
    configs: List[Dict[str, Any]],
    service: RoleModelConfigService = Depends(get_service)
):
    """
    批量更新角色配置
    
    Args:
        configs: 配置列表，每个配置包含 role_id 和其他配置字段
    """
    try:
        result = await service.batch_update_role_configs(configs)
        return ApiResponse.success(
            message=f"批量更新完成: 成功 {len(result['success'])}, 失败 {len(result['failed'])}",
            data=result
        )
    except Exception as e:
        return ApiResponse.error(message=f"批量更新失败: {str(e)}")


# ==================== 预设管理 API ====================

@router.get("/model-presets")
async def get_all_presets(
    preset_type: Optional[str] = Query(None, description="预设类型: system/user"),
    include_inactive: bool = Query(False, description="是否包含非激活预设"),
    service: RoleModelConfigService = Depends(get_service)
):
    """
    获取所有模型选择预设
    
    Args:
        preset_type: 按类型筛选（system/user）
        include_inactive: 是否包含已禁用的预设
    """
    try:
        presets = await service.get_all_presets(preset_type, include_inactive)
        return {"success": True, "data": [p.model_dump() for p in presets], "message": "ok"}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] 获取预设列表失败: {e}\n{error_detail}")
        return {"success": False, "message": f"获取预设列表失败: {str(e)}", "data": []}


@router.get("/model-presets/{preset_id}")
async def get_preset(
    preset_id: str,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    获取单个预设详情
    
    Args:
        preset_id: 预设ID
    """
    try:
        preset = await service.get_preset(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
        return {
            "success": True,
            "data": preset.model_dump(),
            "message": "ok"
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "data": {},
            "message": f"获取预设失败: {str(e)}"
        }


@router.post("/model-presets")
async def create_preset(
    data: ModelSelectionPresetCreate,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    创建新预设
    
    Args:
        data: 预设创建数据
    """
    try:
        preset = await service.create_preset(data)
        dump = preset.model_dump()
        
        return {
            "success": True,
            "data": dump,
            "message": "创建预设成功"
        }
    except Exception as e:
        return {
            "success": False,
            "data": {},
            "message": f"创建预设失败: {str(e)}"
        }


@router.put("/model-presets/{preset_id}")
async def update_preset(
    preset_id: str,
    data: ModelSelectionPresetUpdate,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    更新预设
    
    Args:
        preset_id: 预设ID
        data: 更新数据
    """
    try:
        preset = await service.update_preset(preset_id, data)
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
        return {
            "success": True,
            "message": "更新预设成功",
            "data": preset.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "data": {},
            "message": f"更新预设失败: {str(e)}"
        }


@router.delete("/model-presets/{preset_id}")
async def delete_preset(
    preset_id: str,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    删除预设
    
    Args:
        preset_id: 预设ID
    """
    try:
        success = await service.delete_preset(preset_id)
        if not success:
            raise HTTPException(status_code=404, detail="预设不存在")
        return {
            "success": True,
            "message": "删除预设成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "message": f"删除预设失败: {str(e)}"
        }


@router.post("/model-presets/{preset_id}/apply")
async def apply_preset(
    preset_id: str,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    应用预设到角色配置
    
    Args:
        preset_id: 预设ID
    """
    try:
        result = await service.apply_preset(preset_id)
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": {"applied_configs": result.applied_configs}
            }
        else:
            return {
                "success": False,
                "message": result.message,
                "data": {}
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"应用预设失败: {str(e)}",
            "data": {}
        }


# ==================== 运行时配置 API ====================

@router.get("/model-selection/active")
async def get_active_config():
    """
    获取当前生效的模型配置
    """
    print("[DEBUG] get_active_config 被调用 - 简化版本")
    try:
        service = RoleModelConfigService()
        config = await service.get_active_config()
        return {"success": True, "data": config, "message": "ok"}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] get_active_config 失败: {e}")
        print(f"[ERROR] 堆栈: {error_detail}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=200,
            content={"success": False, "data": {}, "message": f"获取生效配置失败: {str(e)}", "traceback": error_detail}
        )


@router.get("/model-selection/role/{role_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_model_for_role(
    role_id: str,
    service: RoleModelConfigService = Depends(get_service)
):
    """
    获取指定角色的模型配置
    
    按优先级返回：角色特定配置 > 类型默认配置 > 全局默认配置
    
    Args:
        role_id: 角色ID
    """
    try:
        config = await service.get_model_for_role(role_id)
        if not config:
            return ApiResponse.error(message="未找到该角色的配置")
        return ApiResponse.success(data=config.model_dump())
    except Exception as e:
        return ApiResponse.error(message=f"获取角色模型配置失败: {str(e)}")


@router.get("/model-selection/analysis-models")
async def get_analysis_models(
    service: RoleModelConfigService = Depends(get_service)
):
    """
    获取快速分析和深度分析使用的模型
    
    - 快速分析 -> 使用 market 分析师的配置
    - 深度分析 -> 使用 investment_manager 决策者的配置
    """
    try:
        models = await service.get_analysis_models()
        return {
            "success": True,
            "data": {
                "quick_analysis_model": models["quick"]["model_name"],
                "deep_analysis_model": models["deep"]["model_name"]
            },
            "message": "ok"
        }
    except Exception as e:
        return {"success": False, "data": {}, "message": f"获取分析模型失败: {str(e)}"}
