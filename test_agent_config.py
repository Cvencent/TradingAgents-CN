#!/usr/bin/env python3
"""
测试Agent配置功能
"""

import logging
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.mongo_agent_config import MongoAgentConfig
from app.core.database import get_mongo_db_sync

# 初始化日志
logger = get_logger("test_agent_config")
logger.info("🚀 开始测试Agent配置功能")


def test_mongo_agent_config():
    """测试MongoDB Agent配置功能"""
    try:
        # 获取MongoDB数据库连接
        db = get_mongo_db_sync()
        logger.info("✅ 成功获取MongoDB数据库连接")
        
        # 创建MongoAgentConfig实例
        mongo_agent_config = MongoAgentConfig(db)
        logger.info("✅ 成功创建MongoAgentConfig实例")
        
        # 测试初始化默认配置
        logger.info("📋 测试初始化默认Agent配置...")
        success = mongo_agent_config.initialize_default_configs()
        if success:
            logger.info("✅ 初始化默认Agent配置成功")
        else:
            logger.error("❌ 初始化默认Agent配置失败")
        
        # 测试获取所有配置
        logger.info("📋 测试获取所有Agent配置...")
        configs = mongo_agent_config.get_all_agent_configs()
        logger.info(f"✅ 成功获取{len(configs)}个Agent配置")
        
        # 打印配置详情
        for config in configs:
            logger.info(f"📄 Agent配置: {config['agent_id']} - {config['name']}")
            logger.info(f"   描述: {config.get('description', '无')}")
            logger.info(f"   启用: {config.get('enabled', True)}")
            logger.info(f"   版本: {config.get('version', 1)}")
            logger.info("---")
        
        # 测试获取单个配置
        logger.info("📋 测试获取单个Agent配置...")
        for agent_id in ['fundamentals', 'market', 'news']:
            config = mongo_agent_config.get_agent_config(agent_id)
            if config:
                logger.info(f"✅ 成功获取Agent配置: {agent_id}")
            else:
                logger.warning(f"⚠️ 未找到Agent配置: {agent_id}")
        
        logger.info("🎉 所有测试完成")
        return True
        
    except Exception as e:
        logger.error(f"💥 测试失败: {e}")
        return False


if __name__ == "__main__":
    test_mongo_agent_config()
