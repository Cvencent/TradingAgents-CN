"""
工具配置MongoDB操作
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)


class MongoToolConfig:
    """工具配置MongoDB操作类"""
    
    def __init__(self, db):
        """
        初始化工具配置管理器
        
        Args:
            db: MongoDB数据库连接
        """
        self.db = db
        self.collection = db.tool_configs
    
    def get_tool_config(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工具配置
        
        Args:
            tool_id: 工具ID
            
        Returns:
            工具配置字典，如果不存在则返回 None
        """
        try:
            config = self.collection.find_one({"tool_id": tool_id})
            if config:
                config["_id"] = str(config["_id"])
                return config
            return None
        except Exception as e:
            logger.error(f"❌ 获取工具配置失败: {tool_id}, 错误: {e}")
            return None
    
    def get_all_tool_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有工具配置
        
        Returns:
            工具配置列表
        """
        try:
            configs = list(self.collection.find({}))
            for config in configs:
                config["_id"] = str(config["_id"])
            return configs
        except Exception as e:
            logger.error(f"❌ 获取所有工具配置失败: {e}")
            return []
    
    def get_all_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        获取指定分类的工具配置
        
        Args:
            category: 工具分类
            
        Returns:
            指定分类的工具配置列表
        """
        try:
            configs = list(self.collection.find({"category": category}))
            for config in configs:
                config["_id"] = str(config["_id"])
            return configs
        except Exception as e:
            logger.error(f"❌ 获取指定分类工具配置失败: {category}, 错误: {e}")
            return []
    
    def save_tool_config(self, config: Dict[str, Any]) -> bool:
        """
        保存工具配置
        
        Args:
            config: 工具配置字典
            
        Returns:
            是否保存成功
        """
        try:
            current_time = datetime.now().isoformat()
            config["updated_at"] = current_time
            
            tool_id = config.get("tool_id")
            
            if tool_id:
                existing_config = self.collection.find_one({"tool_id": tool_id})
                if existing_config:
                    result = self.collection.update_one(
                        {"tool_id": tool_id},
                        {"$set": config}
                    )
                    if result.modified_count > 0:
                        logger.info(f"✅ 成功更新工具配置: {tool_id}")
                    else:
                        logger.warning(f"⚠️ 工具配置未更新: {tool_id}")
                else:
                    config["created_at"] = current_time
                    result = self.collection.insert_one(config)
                    logger.info(f"✅ 成功创建工具配置: {tool_id}")
                
                return True
            else:
                logger.error(f"❌ 工具配置缺少tool_id: {config}")
                return False
        except Exception as e:
            logger.error(f"❌ 保存工具配置失败: {e}")
            return False
    
    def delete_tool_config(self, tool_id: str) -> bool:
        """
        删除工具配置
        
        Args:
            tool_id: 工具ID
            
        Returns:
            是否删除成功
        """
        try:
            result = self.collection.delete_one({"tool_id": tool_id})
            if result.deleted_count > 0:
                logger.info(f"✅ 成功删除工具配置: {tool_id}")
                return True
            else:
                logger.warning(f"⚠️ 工具配置不存在: {tool_id}")
                return False
        except Exception as e:
            logger.error(f"❌ 删除工具配置失败: {tool_id}, 错误: {e}")
            return False
    
    def initialize_default_tools(self, tool_registry) -> bool:
        """
        初始化默认工具配置
        
        Args:
            tool_registry: 工具注册器实例
            
        Returns:
            是否初始化成功
        """
        try:
            from tradingagents.agents.utils.tool_registry import get_tool_registry
            
            registry = get_tool_registry()
            all_tools = registry.get_all_tools()
            
            for tool_info in all_tools:
                tool_id = tool_info.tool_id
                
                existing_config = self.collection.find_one({"tool_id": tool_id})
                
                if not existing_config:
                    config = {
                        "tool_id": tool_info.tool_id,
                        "name": tool_info.name,
                        "description": tool_info.description,
                        "category": tool_info.category,
                        "parameters": tool_info.parameters,
                        "remarks": tool_info.remarks,
                        "enabled": tool_info.enabled,
                        "created_at": tool_info.created_at,
                        "updated_at": tool_info.updated_at
                    }
                    
                    result = self.collection.insert_one(config)
                    logger.info(f"✅ 成功初始化工具配置: {tool_id}")
                else:
                    logger.info(f"⏭️ 工具配置已存在，跳过: {tool_id}")
            
            return True
        except Exception as e:
            logger.error(f"❌ 初始化默认工具配置失败: {e}")
            return False
    
    def batch_save_tool_configs(self, configs: List[Dict[str, Any]]) -> bool:
        """
        批量保存工具配置
        
        Args:
            configs: 工具配置列表
            
        Returns:
            是否保存成功
        """
        try:
            current_time = datetime.now().isoformat()
            
            for config in configs:
                config["updated_at"] = current_time
                
                tool_id = config.get("tool_id")
                
                if tool_id:
                    existing_config = self.collection.find_one({"tool_id": tool_id})
                    if existing_config:
                        self.collection.update_one(
                            {"tool_id": tool_id},
                            {"$set": config}
                        )
                    else:
                        config["created_at"] = current_time
                        self.collection.insert_one(config)
            
            logger.info(f"✅ 成功批量保存工具配置: {len(configs)} 条")
            return True
        except Exception as e:
            logger.error(f"❌ 批量保存工具配置失败: {e}")
            return False
