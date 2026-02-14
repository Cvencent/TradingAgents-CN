"""
工具配置管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json

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


class ToolTestRequest(BaseModel):
    """工具测试请求模型"""
    parameters: Dict[str, Any] = {}


class ToolTestResponse(BaseModel):
    """工具测试响应模型"""
    success: bool
    message: str
    result: Optional[str] = None
    error: Optional[str] = None

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
        logger.error(f"[X] 获取工具列表失败: {e}", exc_info=True)
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
        logger.error(f"[X] 获取工具详情失败: {e}", exc_info=True)
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
        logger.error(f"[X] 更新工具配置失败: {e}", exc_info=True)
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
        logger.error(f"[X] 初始化默认工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化默认工具配置失败: {str(e)}"
        )


@router.post("/{tool_id}/test", summary="测试工具")
async def test_tool(
    tool_id: str,
    body: Dict[str, Any] = Body(None),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_mongo_db_sync)
):
    """
    测试指定工具的执行结果

    Args:
        tool_id: 工具ID
        body: 请求体，包含参数和test_mode

    Returns:
        工具执行结果
    """
    try:
        mongo_tool_config = MongoToolConfig(db)
        config = mongo_tool_config.get_tool_config(tool_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {tool_id}"
            )

        tool_name = config.get("name", tool_id)
        tool_function = tool_id

        logger.info(f"🔧 [工具测试] 开始测试工具: {tool_name} ({tool_id})")

        params = body.get("parameters", {}) if body else {}
        is_test_mode = body.get("test_mode", False) if body else False

        # 测试模式下跳过耗时操作
        if is_test_mode:
            os.environ["TA_SKIP_GOOGLE_NEWS"] = "true"
            logger.info(f"🔧 [工具测试] 测试模式：跳过Google News")

        result = None
        error_msg = None

        try:
            from tradingagents.agents.utils.agent_utils import Toolkit
            import inspect

            logger.info(f"📊 [工具测试] 查找函数: {tool_function}")
            logger.info(f"📊 [工具测试] Toolkit可用方法: {[m for m in dir(Toolkit) if not m.startswith('_') and callable(getattr(Toolkit, m, None))]}")

            if hasattr(Toolkit, tool_function):
                func = getattr(Toolkit, tool_function)
                if callable(func):
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())

                    kwargs = {}

                    for param_name in param_names:
                        if param_name in params:
                            kwargs[param_name] = params[param_name]

                    logger.info(f"📊 [工具测试] 调用 {tool_function}, 参数: {kwargs}")

                    if inspect.iscoroutinefunction(func):
                        import asyncio
                        result = await func(**kwargs)
                    else:
                        result = func(**kwargs)

                    result = str(result) if result else ""
                else:
                    error_msg = f"工具函数不可调用: {tool_function}"
            else:
                available_methods = [m for m in dir(Toolkit) if not m.startswith('_') and callable(getattr(Toolkit, m, None))]
                error_msg = f"工具函数不存在: {tool_function}，可用方法: {available_methods[:10]}"

        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            logger.error(f"[X] [工具测试] 执行失败: {e}", exc_info=True)

        await log_operation(
            user_id=str(current_user.get("user_id", "")),
            username=current_user.get("username", "unknown"),
            action_type=ActionType.CONFIG_MANAGEMENT,
            action="测试工具",
            details={
                "tool_id": tool_id,
                "tool_name": tool_name,
                "parameters": params,
                "success": result is not None and error_msg is None
            },
            ip_address="",
            user_agent=""
        )

        if result is not None:
            result_str = str(result)
            return ToolTestResponse(
                success=True,
                message=f"工具测试成功",
                result=result_str[:10000] if len(result_str) > 10000 else result_str
            )
        else:
            return ToolTestResponse(
                success=False,
                message=f"工具测试失败",
                error=error_msg
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[X] 工具测试失败: {e}", exc_info=True)
        return ToolTestResponse(
            success=False,
            message=f"工具测试失败",
            error=str(e)
        )
