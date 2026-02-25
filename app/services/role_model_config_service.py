"""
角色模型配置服务
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from app.core.database import get_mongo_db
from app.models.role_model_config import (
    RoleModelConfig, ModelSelectionPreset, AnalysisModelConfig,
    ModelConfigRef, RoleModelConfigRef,
    RoleModelConfigUpdate, RoleModelConfigResponse,
    ModelSelectionPresetCreate, ModelSelectionPresetUpdate,
    ApplyPresetResponse
)
from app.utils.timezone import now_tz

logger = logging.getLogger(__name__)


# 预定义角色
ANALYST_ROLES = [
    {"id": "market", "name": "技术面分析师", "icon": "TrendCharts", "description": "技术分析、价格走势分析"},
    {"id": "fundamentals", "name": "基本面分析师", "icon": "Document", "description": "财务报表、基本面分析"},
    {"id": "capital_flow", "name": "资金流分析师", "icon": "Money", "description": "主力资金、北向资金分析"},
    {"id": "news", "name": "新闻分析师", "icon": "Message", "description": "新闻舆情分析"},
    {"id": "social", "name": "社媒分析师", "icon": "ChatDotRound", "description": "社交媒体情绪分析"},
    {"id": "market_trend", "name": "大盘走势分析师", "icon": "DataLine", "description": "大盘指数、行业分析"},
]

DEBATER_ROLES = [
    {"id": "bull", "name": "多头分析师", "icon": "Top", "description": "看涨观点分析"},
    {"id": "bear", "name": "空头分析师", "icon": "Bottom", "description": "看跌观点分析"},
]

DECISION_ROLES = [
    {"id": "investment_manager", "name": "投资经理", "icon": "User", "description": "投资决策"},
    {"id": "portfolio_manager", "name": "组合经理", "icon": "Collection", "description": "组合管理"},
    {"id": "risk_manager", "name": "风险经理", "icon": "Warning", "description": "风险评估"},
]

ALL_ROLES = {
    "analyst": ANALYST_ROLES,
    "debater": DEBATER_ROLES,
    "decision_maker": DECISION_ROLES,
}


class RoleModelConfigService:
    """角色模型配置服务"""
    
    def __init__(self, db=None):
        self.db = db
    
    async def _get_db(self):
        """获取数据库连接"""
        if self.db is None:
            try:
                self.db = get_mongo_db()
                logger.info("✅ 数据库连接获取成功")
            except Exception as e:
                logger.error(f"❌ 数据库连接获取失败: {e}")
                raise
        return self.db
    
    # ==================== 角色配置管理 ====================
    
    async def get_all_role_configs(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取所有角色配置
        
        Returns:
            按角色类型分组的配置列表
        """
        try:
            logger.info("🔄 开始获取所有角色配置...")
            
            db = await self._get_db()
            logger.info(f"✅ 获取数据库连接成功")
            
            collection = db.role_model_configs
            logger.info(f"✅ 获取集合成功")
            
            # 获取数据库中的配置
            db_configs = {}
            cursor = collection.find({})
            async for doc in cursor:
                logger.debug(f"  找到配置: {doc.get('role_id')}")
                db_configs[doc["role_id"]] = doc
            
            logger.info(f"✅ 从数据库获取了 {len(db_configs)} 个配置")
            
            # 组装结果
            result = {
                "analysts": [],
                "debaters": [],
                "decision_makers": [],
            }
            
            # 分析师
            logger.info(f"🔄 组装分析师配置 ({len(ANALYST_ROLES)} 个)...")
            for role in ANALYST_ROLES:
                config = db_configs.get(role["id"])
                result["analysts"].append(self._format_role_response(role, config, "analyst"))
            
            # 辩论者
            logger.info(f"🔄 组装辩论者配置 ({len(DEBATER_ROLES)} 个)...")
            for role in DEBATER_ROLES:
                config = db_configs.get(role["id"])
                result["debaters"].append(self._format_role_response(role, config, "debater"))
            
            # 决策者
            logger.info(f"🔄 组装决策者配置 ({len(DECISION_ROLES)} 个)...")
            for role in DECISION_ROLES:
                config = db_configs.get(role["id"])
                result["decision_makers"].append(self._format_role_response(role, config, "decision_maker"))
            
            logger.info(f"✅ 成功获取所有角色配置")
            return result
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"❌ 获取所有角色配置失败: {e}")
            logger.error(f"错误详情:\n{error_detail}")
            raise
    
    def _format_role_response(self, role: Dict, config: Optional[Dict], role_type: str) -> Dict[str, Any]:
        """格式化角色响应"""
        if config:
            return {
                "role_id": role["id"],
                "role_name": role["name"],
                "role_type": role_type,
                "icon": role.get("icon", ""),
                "description": role.get("description", ""),
                "current_config": {
                    "id": str(config.get("_id", "")),
                    "provider": config.get("provider", ""),
                    "model_name": config.get("model_name", ""),
                    "model_display_name": config.get("model_display_name"),
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens", 4000),
                    "timeout": config.get("timeout", 180),
                    "is_enabled": config.get("is_enabled", True),
                    "is_default": config.get("is_default", False),
                    "description": config.get("description", ""),
                }
            }
        else:
            # 返回默认配置
            return {
                "role_id": role["id"],
                "role_name": role["name"],
                "role_type": role_type,
                "icon": role.get("icon", ""),
                "description": role.get("description", ""),
                "current_config": None
            }
    
    async def get_role_config(self, role_id: str) -> Optional[RoleModelConfig]:
        """
        获取单个角色配置
        
        Args:
            role_id: 角色ID
            
        Returns:
            角色配置对象
        """
        try:
            db = await self._get_db()
            collection = db.role_model_configs
            
            doc = await collection.find_one({"role_id": role_id})
            if doc:
                return RoleModelConfig(**doc)
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取角色配置失败: {e}")
            raise
    
    # ==================== 预设管理 ====================
    
    async def get_all_presets(self, preset_type: Optional[str] = None, include_inactive: bool = False) -> List[ModelSelectionPreset]:
        """
        获取所有预设
        
        Args:
            preset_type: 预设类型筛选（system/user）
            include_inactive: 是否包含非激活预设
            
        Returns:
            预设列表
        """
        try:
            db = await self._get_db()
            collection = db.model_selection_presets
            
            # 构建查询条件
            query = {}
            if preset_type:
                query["preset_type"] = preset_type
            if not include_inactive:
                query["is_active"] = True
            
            presets = []
            async for doc in collection.find(query).sort("created_at", -1):
                try:
                    # 确保必需的字段存在
                    if "default_provider" not in doc or "default_model" not in doc:
                        logger.warning(f"⚠️ 预设缺少必需字段，跳过: {doc.get('name', 'unknown')}")
                        continue
                    presets.append(ModelSelectionPreset(**doc))
                except Exception as e:
                    logger.warning(f"⚠️ 解析预设失败，跳过: {e}")
                    continue
            
            return presets
            
        except Exception as e:
            logger.error(f"❌ 获取预设列表失败: {e}")
            raise
    
    async def get_preset(self, preset_id: str) -> Optional[ModelSelectionPreset]:
        """
        获取单个预设
        
        Args:
            preset_id: 预设ID
            
        Returns:
            预设对象
        """
        try:
            db = await self._get_db()
            collection = db.model_selection_presets
            
            # 优先尝试字符串查询（兼容现有数据），如果失败再尝试 ObjectId
            doc = await collection.find_one({"_id": preset_id})
            
            if not doc:
                try:
                    doc = await collection.find_one({"_id": ObjectId(preset_id)})
                except:
                    pass
            
            if doc:
                # 确保 _id 是字符串
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                return ModelSelectionPreset(**doc)
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取预设失败 [{preset_id}]: {e}")
            raise
    
    async def create_preset(self, data: ModelSelectionPresetCreate, user_id: Optional[str] = None) -> ModelSelectionPreset:
        """
        创建预设
        
        Args:
            data: 预设创建数据
            user_id: 用户ID（可选）
            
        Returns:
            创建的预设
        """
        try:
            db = await self._get_db()
            collection = db.model_selection_presets
            
            preset = ModelSelectionPreset(
                name=data.name,
                description=data.description,
                preset_type="user",
                role_configs=data.role_configs,
                default_provider=data.default_provider,
                default_model=data.default_model,
                is_active=True,
                is_system=False,
                created_by=user_id,
            )
            
            result = await collection.insert_one(preset.model_dump(by_alias=True))
            doc = await collection.find_one({"_id": result.inserted_id})
            
            # 确保 _id 是字符串
            if doc and "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
            logger.info(f"✅ 创建预设成功: {data.name}")
            return ModelSelectionPreset(**doc)
            
        except Exception as e:
            logger.error(f"❌ 创建预设失败: {e}")
            raise
    
    async def update_preset(self, preset_id: str, data: ModelSelectionPresetUpdate) -> Optional[ModelSelectionPreset]:
        """
        更新预设
        
        Args:
            preset_id: 预设ID
            data: 更新数据
            
        Returns:
            更新后的预设
        """
        try:
            db = await self._get_db()
            collection = db.model_selection_presets
            
            # 优先尝试字符串查询（兼容现有数据）
            existing = await collection.find_one({"_id": preset_id})
            if not existing:
                try:
                    existing = await collection.find_one({"_id": ObjectId(preset_id)})
                except:
                    pass
            
            if not existing:
                return None
            
            if existing.get("is_system", False):
                raise ValueError("不能修改系统预设")
            
            # 构建更新数据
            update_data = {"updated_at": now_tz()}
            if data.name is not None:
                update_data["name"] = data.name
            if data.description is not None:
                update_data["description"] = data.description
            if data.role_configs is not None:
                update_data["role_configs"] = {k: v.model_dump() for k, v in data.role_configs.items()}
            if data.default_provider is not None:
                update_data["default_provider"] = data.default_provider
            if data.default_model is not None:
                update_data["default_model"] = data.default_model
            if data.is_active is not None:
                update_data["is_active"] = data.is_active
            
            # 优先使用字符串更新
            result = await collection.update_one(
                {"_id": preset_id},
                {"$set": update_data}
            )
            if result.matched_count == 0:
                # 如果字符串更新失败，尝试 ObjectId
                await collection.update_one(
                    {"_id": ObjectId(preset_id)},
                    {"$set": update_data}
                )
            
            # 查询时优先使用字符串
            doc = await collection.find_one({"_id": preset_id})
            if not doc:
                try:
                    doc = await collection.find_one({"_id": ObjectId(preset_id)})
                except:
                    pass
            if doc:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            logger.info(f"✅ 更新预设成功: {preset_id}")
            return ModelSelectionPreset(**doc)
            
        except Exception as e:
            logger.error(f"❌ 更新预设失败 [{preset_id}]: {e}")
            raise
    
    async def delete_preset(self, preset_id: str) -> bool:
        """
        删除预设
        
        Args:
            preset_id: 预设ID
            
        Returns:
            是否删除成功
        """
        try:
            db = await self._get_db()
            collection = db.model_selection_presets
            
            # 优先尝试字符串查询（兼容现有数据）
            existing = await collection.find_one({"_id": preset_id})
            if not existing:
                try:
                    existing = await collection.find_one({"_id": ObjectId(preset_id)})
                except:
                    pass
            
            if not existing:
                return False
            
            if existing.get("is_system", False):
                raise ValueError("不能删除系统预设")
            
            # 优先使用字符串删除
            result = await collection.delete_one({"_id": preset_id})
            if result.deleted_count == 0:
                # 如果字符串删除失败，尝试 ObjectId
                result = await collection.delete_one({"_id": ObjectId(preset_id)})
            
            if result.deleted_count > 0:
                logger.info(f"✅ 删除预设成功: {preset_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ 删除预设失败 [{preset_id}]: {e}")
            raise
    
    async def apply_preset(self, preset_id: str, user_id: Optional[str] = None) -> ApplyPresetResponse:
        """
        应用预设到角色配置
        
        Args:
            preset_id: 预设ID
            user_id: 用户ID（可选）
            
        Returns:
            应用结果
        """
        try:
            # 获取预设
            preset = await self.get_preset(preset_id)
            if not preset:
                return ApplyPresetResponse(
                    success=False,
                    message="预设不存在",
                    applied_configs=0
                )
            
            db = await self._get_db()
            role_collection = db.role_model_configs
            
            applied_count = 0
            
            # 应用角色配置
            for role_id, config_ref in preset.role_configs.items():
                role_info = self._get_role_info(role_id)
                if not role_info:
                    continue
                
                # 检查是否已存在
                existing = await role_collection.find_one({"role_id": role_id})
                
                if existing:
                    # 更新现有配置
                    await role_collection.update_one(
                        {"role_id": role_id},
                        {"$set": {
                            "provider": config_ref.provider,
                            "model_name": config_ref.model_name,
                            "temperature": config_ref.temperature,
                            "max_tokens": config_ref.max_tokens,
                            "updated_at": now_tz(),
                        }}
                    )
                else:
                    # 创建新配置
                    new_config = RoleModelConfig(
                        role_id=role_id,
                        role_type=role_info["type"],
                        role_name=role_info["name"],
                        provider=config_ref.provider,
                        model_name=config_ref.model_name,
                        temperature=config_ref.temperature,
                        max_tokens=config_ref.max_tokens,
                        is_enabled=True,
                    )
                    await role_collection.insert_one(new_config.model_dump(by_alias=True))
                
                applied_count += 1
            
            # 如果预设有默认模型，将其应用到所有具体角色
            if preset.default_provider and preset.default_model:
                role_mappings = [
                    (ANALYST_ROLES, "analyst"),
                    (DEBATER_ROLES, "debater"),
                    (DECISION_ROLES, "decision_maker")
                ]
                for roles, role_type in role_mappings:
                    for role in roles:
                        # 检查是否已存在该角色的配置
                        existing = await role_collection.find_one({"role_id": role["id"]})
                        
                        if existing:
                            # 更新现有配置
                            await role_collection.update_one(
                                {"role_id": role["id"]},
                                {"$set": {
                                    "provider": preset.default_provider,
                                    "model_name": preset.default_model,
                                    "updated_at": now_tz(),
                                }}
                            )
                        else:
                            # 创建新配置
                            new_config = RoleModelConfig(
                                role_id=role["id"],
                                role_type=role_type,
                                role_name=role["name"],
                                provider=preset.default_provider,
                                model_name=preset.default_model,
                                temperature=0.7,
                                max_tokens=4000,
                                is_enabled=True,
                            )
                            await role_collection.insert_one(new_config.model_dump(by_alias=True))
                        
                        applied_count += 1
            
            logger.info(f"✅ 应用预设成功: {preset.name}, 共应用 {applied_count} 个角色配置")
            
            return ApplyPresetResponse(
                success=True,
                message=f"预设 '{preset.name}' 已应用（默认模型: {preset.default_provider}/{preset.default_model}）",
                applied_configs=applied_count
            )
            
        except Exception as e:
            logger.error(f"❌ 应用预设失败 [{preset_id}]: {e}")
            return ApplyPresetResponse(
                success=False,
                message=f"应用失败: {str(e)}",
                applied_configs=0
            )
    
    # ==================== 运行时配置 ====================
    
    async def get_active_config(self) -> Dict[str, Any]:
        """
        获取当前生效的完整配置
        
        Returns:
            包含所有角色类型的配置
        """
        try:
            logger.info("🔄 get_active_config: 开始获取配置...")
            
            # 获取所有角色配置
            all_configs = await self.get_all_role_configs()
            logger.info(f"🔄 get_active_config: all_configs keys = {all_configs.keys()}")
            logger.info(f"🔄 get_active_config: all_configs = {all_configs}")
            
            # 检查第一个分析师的配置
            if all_configs.get("analysts"):
                first_analyst = all_configs["analysts"][0]
                logger.info(f"🔄 get_active_config: first_analyst = {first_analyst}")
                logger.info(f"🔄 get_active_config: current_config = {first_analyst.get('current_config')}")
            
            # 组装运行时配置
            result = {
                "preset_id": None,
                "preset_name": None,
                "configs": {
                    "analysts": {},
                    "debaters": {},
                    "decision_makers": {},
                },
                "default_model": None,
            }
            
            logger.info(f"🔄 get_active_config: 基础 result 创建完成")
            
            # 遍历每个角色类型
            for role_type, configs in all_configs.items():
                logger.info(f"🔄 get_active_config: 处理 role_type = {role_type}, count = {len(configs)}")
                
                for config in configs:
                    role_id = config.get("role_id")
                    logger.info(f"🔄 get_active_config: 处理 role_id = {role_id}")
                    
                    if role_id:
                        current = config.get("current_config", {})
                        logger.info(f"🔄 get_active_config: current = {current}")
                        
                        model_info = current.get("model", {})
                        logger.info(f"🔄 get_active_config: model_info = {model_info}")
                        
                        model_config_ref = None
                        if model_info:
                            model_config_ref = ModelConfigRef(
                                provider=model_info.get("provider", "dashscope"),
                                model_name=model_info.get("model_name", "qwen-max"),
                                temperature=model_info.get("temperature", 0.7),
                                max_tokens=model_info.get("max_tokens", 4000),
                            )
                            logger.info(f"🔄 get_active_config: 创建 model_config_ref 成功")
                        
                        if role_type == "analysts":
                            result["configs"]["analysts"][role_id] = model_config_ref
                        elif role_type == "debaters":
                            result["configs"]["debaters"][role_id] = model_config_ref
                        elif role_type == "decision_makers":
                            result["configs"]["decision_makers"][role_id] = model_config_ref
            
            logger.info(f"🔄 get_active_config: 处理完成, result = {result}")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"❌ get_active_config 异常: {e}")
            logger.error(f"堆栈: {traceback.format_exc()}")
            raise
    
    async def get_model_for_role(self, role_id: str) -> Optional[ModelConfigRef]:
        """
        获取指定角色的模型配置
        
        配置优先级：
        1. 角色特定配置
        2. 角色类型默认配置
        3. 全局默认配置
        
        Args:
            role_id: 角色ID
            
        Returns:
            模型配置
        """
        try:
            # 1. 查找角色特定配置
            role_config = await self.get_role_config(role_id)
            if role_config and role_config.is_enabled:
                return ModelConfigRef(
                    provider=role_config.provider,
                    model_name=role_config.model_name,
                    temperature=role_config.temperature,
                    max_tokens=role_config.max_tokens,
                    timeout=role_config.timeout,
                )
            
            # 2. 查找角色类型默认配置
            role_info = self._get_role_info(role_id)
            if role_info:
                db = await self._get_db()
                collection = db.role_model_configs
                
                default_config = await collection.find_one({
                    "role_type": role_info["type"],
                    "is_default": True,
                    "is_enabled": True,
                })
                
                if default_config:
                    return ModelConfigRef(
                        provider=default_config["provider"],
                        model_name=default_config["model_name"],
                        temperature=default_config.get("temperature"),
                        max_tokens=default_config.get("max_tokens"),
                        timeout=default_config.get("timeout"),
                    )
            
            # 3. 使用全局默认配置（从系统设置获取）
            # TODO: 从系统设置获取全局默认配置
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取角色模型配置失败 [{role_id}]: {e}")
            raise
            
        except Exception as e:
            logger.error(f"❌ 获取角色配置失败 [{role_id}]: {e}")
            raise
    
    async def get_analysis_models(self) -> Dict[str, Dict[str, str]]:
        """
        获取快速分析和深度分析使用的模型
        
        映射关系：
        - 快速分析 -> 使用第一个分析师角色(market)的配置
        - 深度分析 -> 使用第一个决策者角色(investment_manager)的配置
        
        Returns:
            包含 quick 和 deep 模型信息的字典
        """
        try:
            db = await self._get_db()
            collection = db.role_model_configs
            
            result = {
                "quick": {"provider": None, "model_name": None},
                "deep": {"provider": None, "model_name": None}
            }
            
            # 快速分析：使用 market 分析师的配置
            quick_config = await collection.find_one({"role_id": "market", "is_enabled": True})
            if quick_config:
                result["quick"]["provider"] = quick_config.get("provider")
                result["quick"]["model_name"] = quick_config.get("model_name")
            
            # 深度分析：使用 investment_manager 决策者的配置
            deep_config = await collection.find_one({"role_id": "investment_manager", "is_enabled": True})
            if deep_config:
                result["deep"]["provider"] = deep_config.get("provider")
                result["deep"]["model_name"] = deep_config.get("model_name")
            
            logger.info(f"🔍 获取分析模型: quick={result['quick']['model_name']}, deep={result['deep']['model_name']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取分析模型失败: {e}")
            raise
    
    async def update_role_config(self, role_id: str, update: RoleModelConfigUpdate, user_id: Optional[str] = None) -> RoleModelConfig:
        """
        更新角色模型配置
        
        Args:
            role_id: 角色ID
            update: 更新数据
            user_id: 用户ID（可选）
            
        Returns:
            更新后的配置
        """
        try:
            db = await self._get_db()
            collection = db.role_model_configs
            
            # 查找角色信息
            role_info = self._get_role_info(role_id)
            if not role_info:
                raise ValueError(f"未知的角色ID: {role_id}")
            
            # 检查是否已存在
            existing = await collection.find_one({"role_id": role_id})
            
            now = now_tz()
            
            if existing:
                # 更新现有配置
                update_data = {
                    "provider": update.provider,
                    "model_name": update.model_name,
                    "model_display_name": update.model_display_name,
                    "temperature": update.temperature,
                    "max_tokens": update.max_tokens,
                    "timeout": update.timeout,
                    "is_enabled": update.is_enabled,
                    "description": update.description,
                    "updated_at": now,
                }
                
                await collection.update_one(
                    {"role_id": role_id},
                    {"$set": update_data}
                )
                
                # 获取更新后的配置
                doc = await collection.find_one({"role_id": role_id})
                logger.info(f"✅ 更新角色配置成功: {role_id}")
                
            else:
                # 创建新配置
                config = RoleModelConfig(
                    role_id=role_id,
                    role_type=role_info["type"],
                    role_name=role_info["name"],
                    provider=update.provider,
                    model_name=update.model_name,
                    model_display_name=update.model_display_name,
                    temperature=update.temperature,
                    max_tokens=update.max_tokens,
                    timeout=update.timeout,
                    is_enabled=update.is_enabled,
                    description=update.description,
                    created_by=user_id,
                )
                
                result = await collection.insert_one(config.model_dump(by_alias=True))
                doc = await collection.find_one({"_id": result.inserted_id})
                logger.info(f"✅ 创建角色配置成功: {role_id}")
            
            return RoleModelConfig(**doc)
            
        except Exception as e:
            logger.error(f"❌ 更新角色配置失败 [{role_id}]: {e}")
            raise
    
    async def batch_update_role_configs(self, configs: List[Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        批量更新角色配置
        
        Args:
            configs: 配置列表，每个包含 role_id 和配置数据
            user_id: 用户ID（可选）
            
        Returns:
            批量更新结果
        """
        try:
            results = {
                "success": [],
                "failed": [],
            }
            
            for config_item in configs:
                # 处理 Pydantic 模型或字典
                if hasattr(config_item, 'dict'):
                    config_data = config_item.dict()
                elif hasattr(config_item, 'model_dump'):
                    config_data = config_item.model_dump()
                else:
                    config_data = dict(config_item)
                
                role_id = config_data.get("role_id")
                if not role_id:
                    results["failed"].append({"error": "缺少 role_id"})
                    continue
                
                try:
                    # 移除 role_id，只保留配置字段
                    update_data = {k: v for k, v in config_data.items() if k != "role_id"}
                    update = RoleModelConfigUpdate(**update_data)
                    await self.update_role_config(role_id, update, user_id)
                    results["success"].append(role_id)
                except Exception as e:
                    results["failed"].append({"role_id": role_id, "error": str(e)})
            
            logger.info(f"✅ 批量更新完成: 成功 {len(results['success'])}, 失败 {len(results['failed'])}")
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量更新角色配置失败: {e}")
            raise
    
    def _get_role_info(self, role_id: str) -> Optional[Dict[str, str]]:
        """获取角色信息"""
        for role_type, roles in ALL_ROLES.items():
            for role in roles:
                if role["id"] == role_id:
                    return {
                        "id": role["id"],
                        "name": role["name"],
                        "type": role_type,
                        "icon": role.get("icon", ""),
                        "description": role.get("description", ""),
                    }
        return None
