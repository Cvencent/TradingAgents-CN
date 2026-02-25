"""
角色模型配置数据库初始化脚本
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from app.core.database import get_mongo_db
from app.models.role_model_config import RoleModelConfig, ModelSelectionPreset, RoleModelConfigRef

logger = logging.getLogger(__name__)


# 预定义角色
ANALYST_ROLES = [
    {"id": "market", "name": "技术面分析师", "icon": "TrendCharts", "description": "技术分析、价格走势分析"},
    {"id": "fundamentals", "name": "基本面分析师", "icon": "Document", "description": "财务报表、基本面分析"},
    {"id": "capital_flow", "name": "资金流分析师", "icon": "Money", "description": "主力资金、北向资金分析"},
    {"id": "news", "name": "新闻分析师", "icon": "News", "description": "新闻舆情分析"},
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

# 默认模型配置
DEFAULT_MODEL_CONFIG = {
    "provider": "openai",
    "model_name": "gpt-3.5-turbo",
    "model_display_name": "GPT-3.5 Turbo",
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout": 180,
}

# 系统预设
SYSTEM_PRESETS = [
    {
        "name": "经济型",
        "description": "使用成本较低的模型，适合快速分析",
        "preset_type": "system",
        "role_configs": {},
        "default_provider": "openai",
        "default_model": "gpt-3.5-turbo",
        "is_system": True,
    },
    {
        "name": "平衡型",
        "description": "在成本和性能之间取得平衡",
        "preset_type": "system",
        "role_configs": {
            "market": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7},
            "fundamentals": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7},
        },
        "default_provider": "openai",
        "default_model": "gpt-3.5-turbo",
        "is_system": True,
    },
    {
        "name": "高性能",
        "description": "使用最强模型，适合深度分析",
        "preset_type": "system",
        "role_configs": {
            "market": {"provider": "openai", "model_name": "gpt-4o", "temperature": 0.5},
            "fundamentals": {"provider": "openai", "model_name": "gpt-4o", "temperature": 0.5},
            "capital_flow": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7},
            "news": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7},
            "social": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7},
            "market_trend": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.7},
            "bull": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.8},
            "bear": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.8},
            "investment_manager": {"provider": "openai", "model_name": "gpt-4o", "temperature": 0.4},
            "portfolio_manager": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.5},
            "risk_manager": {"provider": "openai", "model_name": "gpt-4", "temperature": 0.5},
        },
        "default_provider": "openai",
        "default_model": "gpt-4",
        "is_system": True,
    },
]


async def init_role_model_configs():
    """初始化角色模型配置集合"""
    try:
        db = get_mongo_db()
        
        # 创建集合（如果不存在）
        if "role_model_configs" not in await db.list_collection_names():
            await db.create_collection("role_model_configs")
            logger.info("✅ 创建集合: role_model_configs")
        
        collection = db.role_model_configs
        
        # 检查是否已有数据
        existing_count = await collection.count_documents({})
        if existing_count > 0:
            logger.info(f"⚠️ 角色模型配置集合已有 {existing_count} 条数据，跳过初始化")
            return
        
        # 初始化分析师角色配置
        for role in ANALYST_ROLES:
            config = RoleModelConfig(
                role_id=role["id"],
                role_type="analyst",
                role_name=role["name"],
                provider=DEFAULT_MODEL_CONFIG["provider"],
                model_name=DEFAULT_MODEL_CONFIG["model_name"],
                model_display_name=DEFAULT_MODEL_CONFIG["model_display_name"],
                temperature=DEFAULT_MODEL_CONFIG["temperature"],
                max_tokens=DEFAULT_MODEL_CONFIG["max_tokens"],
                timeout=DEFAULT_MODEL_CONFIG["timeout"],
                is_enabled=True,
                is_default=False,
                description=role.get("description", ""),
            )
            await collection.insert_one(config.model_dump(by_alias=True))
            logger.info(f"✅ 初始化分析师角色配置: {role['name']}")
        
        # 初始化辩论者角色配置
        for role in DEBATER_ROLES:
            config = RoleModelConfig(
                role_id=role["id"],
                role_type="debater",
                role_name=role["name"],
                provider=DEFAULT_MODEL_CONFIG["provider"],
                model_name=DEFAULT_MODEL_CONFIG["model_name"],
                model_display_name=DEFAULT_MODEL_CONFIG["model_display_name"],
                temperature=DEFAULT_MODEL_CONFIG["temperature"],
                max_tokens=DEFAULT_MODEL_CONFIG["max_tokens"],
                timeout=DEFAULT_MODEL_CONFIG["timeout"],
                is_enabled=True,
                is_default=False,
                description=role.get("description", ""),
            )
            await collection.insert_one(config.model_dump(by_alias=True))
            logger.info(f"✅ 初始化辩论者角色配置: {role['name']}")
        
        # 初始化决策者角色配置
        for role in DECISION_ROLES:
            config = RoleModelConfig(
                role_id=role["id"],
                role_type="decision_maker",
                role_name=role["name"],
                provider=DEFAULT_MODEL_CONFIG["provider"],
                model_name=DEFAULT_MODEL_CONFIG["model_name"],
                model_display_name=DEFAULT_MODEL_CONFIG["model_display_name"],
                temperature=DEFAULT_MODEL_CONFIG["temperature"],
                max_tokens=DEFAULT_MODEL_CONFIG["max_tokens"],
                timeout=DEFAULT_MODEL_CONFIG["timeout"],
                is_enabled=True,
                is_default=False,
                description=role.get("description", ""),
            )
            await collection.insert_one(config.model_dump(by_alias=True))
            logger.info(f"✅ 初始化决策者角色配置: {role['name']}")
        
        logger.info(f"✅ 角色模型配置初始化完成，共初始化 {len(ANALYST_ROLES) + len(DEBATER_ROLES) + len(DECISION_ROLES)} 个角色")
        
    except Exception as e:
        logger.error(f"❌ 初始化角色模型配置失败: {e}")
        raise


async def init_model_selection_presets():
    """初始化模型选择预设集合"""
    try:
        db = get_mongo_db()
        
        # 创建集合（如果不存在）
        if "model_selection_presets" not in await db.list_collection_names():
            await db.create_collection("model_selection_presets")
            logger.info("✅ 创建集合: model_selection_presets")
        
        collection = db.model_selection_presets
        
        # 检查是否已有系统预设
        existing_system = await collection.count_documents({"is_system": True})
        if existing_system > 0:
            logger.info(f"⚠️ 模型选择预设集合已有 {existing_system} 个系统预设，跳过初始化")
            return
        
        # 初始化系统预设
        for preset_data in SYSTEM_PRESETS:
            # 转换 role_configs 为 RoleModelConfigRef 对象
            role_configs = {}
            for role_id, config in preset_data.get("role_configs", {}).items():
                role_configs[role_id] = RoleModelConfigRef(**config)
            
            preset = ModelSelectionPreset(
                name=preset_data["name"],
                description=preset_data["description"],
                preset_type=preset_data["preset_type"],
                role_configs=role_configs,
                default_provider=preset_data["default_provider"],
                default_model=preset_data["default_model"],
                is_active=True,
                is_system=preset_data["is_system"],
            )
            await collection.insert_one(preset.model_dump(by_alias=True))
            logger.info(f"✅ 初始化系统预设: {preset_data['name']}")
        
        logger.info(f"✅ 模型选择预设初始化完成，共初始化 {len(SYSTEM_PRESETS)} 个预设")
        
    except Exception as e:
        logger.error(f"❌ 初始化模型选择预设失败: {e}")
        raise


async def create_indexes():
    """创建索引"""
    try:
        db = get_mongo_db()
        
        # role_model_configs 索引
        if "role_model_configs" in await db.list_collection_names():
            await db.role_model_configs.create_index("role_id", unique=True)
            await db.role_model_configs.create_index("role_type")
            await db.role_model_configs.create_index("is_enabled")
            logger.info("✅ 创建索引: role_model_configs")
        
        # model_selection_presets 索引
        if "model_selection_presets" in await db.list_collection_names():
            await db.model_selection_presets.create_index("name")
            await db.model_selection_presets.create_index("preset_type")
            await db.model_selection_presets.create_index("is_system")
            logger.info("✅ 创建索引: model_selection_presets")
        
    except Exception as e:
        logger.error(f"❌ 创建索引失败: {e}")
        raise


async def init_all():
    """初始化所有角色模型配置相关集合"""
    logger.info("🚀 开始初始化角色模型配置...")
    
    await init_role_model_configs()
    await init_model_selection_presets()
    await create_indexes()
    
    logger.info("✅ 角色模型配置初始化完成")


# 用于命令行直接运行
if __name__ == "__main__":
    asyncio.run(init_all())
