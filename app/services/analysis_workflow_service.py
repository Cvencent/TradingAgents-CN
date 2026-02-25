"""分析流程配置 MongoDB 操作服务"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from tradingagents.utils.logging_init import get_logger

logger = get_logger("default")


class MongoAnalysisWorkflowConfig:
    """分析流程配置 MongoDB 操作类"""
    
    def __init__(self, db):
        """
        初始化 MongoDB 分析流程配置操作
        
        Args:
            db: MongoDB 数据库连接
        """
        self.db = db
        self.collection = db.analysis_workflow_configs
        
    def get_workflow_config(self, config_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定流程配置
        
        Args:
            config_id: 配置 ID
            user_id: 用户 ID
            
        Returns:
            配置字典，如果不存在返回 None
        """
        try:
            config = self.collection.find_one({
                "_id": config_id,
                "user_id": user_id
            })
            if config:
                if "_id" in config:
                    config["_id"] = str(config["_id"])
                logger.info(f"✅ 成功获取流程配置: {config_id}")
                return config
            logger.warning(f"⚠️ 未找到流程配置: {config_id}")
            return None
        except Exception as e:
            logger.error(f"[X] 获取流程配置失败: {e}")
            return None
    
    def get_all_workflow_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有流程配置（包括用户配置和系统预设）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            配置列表
        """
        try:
            configs = []
            
            # 获取用户配置
            for config in self.collection.find({"user_id": user_id}):
                if "_id" in config:
                    config["_id"] = str(config["_id"])
                configs.append(config)
            
            # 获取系统预设（如果没有用户配置对应级别，则显示系统预设）
            user_levels = {config.get("analysis_level") for config in configs}
            for config in self.collection.find({"is_system": True}):
                if "_id" in config:
                    config["_id"] = str(config["_id"])
                # 只添加用户没有对应级别的系统预设
                if config.get("analysis_level") not in user_levels:
                    configs.append(config)
            
            # 按分析级别排序
            configs.sort(key=lambda x: x.get("analysis_level", 0))
            
            logger.info(f"✅ 成功获取所有流程配置，共 {len(configs)} 个")
            return configs
        except Exception as e:
            logger.error(f"[X] 获取所有流程配置失败: {e}")
            return []
    
    def save_workflow_config(self, config: Dict[str, Any], user_id: str) -> bool:
        """
        保存流程配置
        
        Args:
            config: 配置字典
            user_id: 用户 ID
            
        Returns:
            是否保存成功
        """
        try:
            current_time = datetime.now().isoformat()
            config["updated_at"] = current_time
            
            if "_id" not in config:
                config["created_at"] = current_time
                config["user_id"] = user_id
            
            config_id = config.get("_id") or config.get("id")
            
            if config_id:
                # 将字符串 ID 转换为 ObjectId
                try:
                    object_id = ObjectId(config_id)
                except:
                    object_id = config_id
                
                # 移除 _id 字段避免更新冲突
                update_data = config.copy()
                if "_id" in update_data:
                    del update_data["_id"]
                if "id" in update_data:
                    del update_data["id"]
                
                result = self.collection.update_one(
                    {"_id": object_id, "user_id": user_id},
                    {"$set": update_data}
                )
                if result.modified_count > 0:
                    logger.info(f"✅ 成功更新流程配置: {config_id}")
                else:
                    logger.warning(f"⚠️ 流程配置未更新: {config_id}")
            else:
                result = self.collection.insert_one(config)
                logger.info(f"✅ 成功创建流程配置: {result.inserted_id}")
            
            return True
        except Exception as e:
            logger.error(f"[X] 保存流程配置失败: {e}")
            return False
    
    def delete_workflow_config(self, config_id: str, user_id: str) -> bool:
        """
        删除流程配置
        
        Args:
            config_id: 配置 ID
            user_id: 用户 ID
            
        Returns:
            是否删除成功
        """
        try:
            # 将字符串 ID 转换为 ObjectId
            try:
                object_id = ObjectId(config_id)
            except:
                # 如果转换失败，直接使用字符串
                object_id = config_id
            
            result = self.collection.delete_one({
                "_id": object_id,
                "user_id": user_id
            })
            if result.deleted_count == 0:
                logger.warning(f"⚠️ 未找到要删除的流程配置: {config_id}")
                return False
            logger.info(f"✅ 成功删除流程配置: {config_id}")
            return True
        except Exception as e:
            logger.error(f"[X] 删除流程配置失败: {e}")
            return False
    
    def set_default_config(self, user_id: str, config_id: str) -> bool:
        """
        设置默认流程配置
        
        Args:
            user_id: 用户 ID
            config_id: 配置 ID
            
        Returns:
            是否设置成功
        """
        try:
            self.collection.update_many(
                {"user_id": user_id},
                {"$set": {"is_default": False}}
            )
            
            result = self.collection.update_one(
                {"_id": config_id, "user_id": user_id},
                {"$set": {"is_default": True}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ 成功设置默认流程配置: {config_id}")
                return True
            else:
                logger.warning(f"⚠️ 未找到要设置的流程配置: {config_id}")
                return False
        except Exception as e:
            logger.error(f"[X] 设置默认流程配置失败: {e}")
            return False
    
    def get_default_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取默认流程配置（已废弃，请使用 get_config_by_level）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            默认配置字典，如果不存在返回 None
        """
        try:
            config = self.collection.find_one({
                "user_id": user_id,
                "is_default": True
            })
            if config:
                if "_id" in config:
                    config["_id"] = str(config["_id"])
                logger.info(f"✅ 成功获取默认流程配置")
                return config
            logger.warning(f"⚠️ 未找到默认流程配置")
            return None
        except Exception as e:
            logger.error(f"[X] 获取默认流程配置失败: {e}")
            return None
    
    def get_config_by_level(self, user_id: str, analysis_level: int) -> Optional[Dict[str, Any]]:
        """
        根据分析级别获取流程配置
        
        Args:
            user_id: 用户 ID
            analysis_level: 分析级别（1-5）
            
        Returns:
            配置字典，如果不存在返回 None
        """
        try:
            config = self.collection.find_one({
                "user_id": user_id,
                "analysis_level": analysis_level
            })
            if config:
                if "_id" in config:
                    config["_id"] = str(config["_id"])
                logger.info(f"✅ 成功获取级别 {analysis_level} 的流程配置")
                return config
            
            logger.info(f"ℹ️ 未找到级别 {analysis_level} 的用户配置，尝试查找系统预设")
            config = self.collection.find_one({
                "is_system": True,
                "analysis_level": analysis_level
            })
            if config:
                if "_id" in config:
                    config["_id"] = str(config["_id"])
                logger.info(f"✅ 成功获取级别 {analysis_level} 的系统预设")
                return config
            
            logger.warning(f"⚠️ 未找到级别 {analysis_level} 的流程配置")
            return None
        except Exception as e:
            logger.error(f"[X] 获取级别 {analysis_level} 的流程配置失败: {e}")
            return None
    
    def set_default_config_by_level(self, user_id: str, config_id: str, analysis_level: int) -> bool:
        """
        设置指定分析级别的默认流程配置
        
        Args:
            user_id: 用户 ID
            config_id: 配置 ID
            analysis_level: 分析级别（1-5）
            
        Returns:
            是否设置成功
        """
        try:
            result = self.collection.update_one(
                {"_id": config_id, "user_id": user_id},
                {"$set": {"analysis_level": analysis_level}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ 成功将配置 {config_id} 设置为级别 {analysis_level} 的默认配置")
                return True
            else:
                logger.warning(f"⚠️ 未找到要设置的流程配置: {config_id}")
                return False
        except Exception as e:
            logger.error(f"[X] 设置级别 {analysis_level} 的默认流程配置失败: {e}")
            return False
    
    def initialize_system_presets(self) -> bool:
        """
        初始化系统预设流程配置
        
        Returns:
            是否初始化成功
        """
        try:
            presets = [
                {
                    "name": "快速分析",
                    "description": "快速分析，适合快速查看股票概况",
                    "analysis_level": 1,
                    "debate_rounds": 1,
                    "risk_discussion_rounds": 1,
                    "debate_timeout": 300,
                    "risk_timeout": 120,
                    "enable_sentiment": False,
                    "enable_risk_assessment": False,
                    "is_system": True,
                    "is_default": False
                },
                {
                    "name": "基础分析",
                    "description": "基础分析，常规投资决策",
                    "analysis_level": 2,
                    "debate_rounds": 1,
                    "risk_discussion_rounds": 1,
                    "debate_timeout": 300,
                    "risk_timeout": 120,
                    "enable_sentiment": True,
                    "enable_risk_assessment": True,
                    "is_system": True,
                    "is_default": False
                },
                {
                    "name": "标准分析",
                    "description": "标准分析，平衡速度和深度",
                    "analysis_level": 3,
                    "debate_rounds": 1,
                    "risk_discussion_rounds": 2,
                    "debate_timeout": 300,
                    "risk_timeout": 120,
                    "enable_sentiment": True,
                    "enable_risk_assessment": True,
                    "is_system": True,
                    "is_default": False
                },
                {
                    "name": "深度分析",
                    "description": "深度分析，多轮辩论和风险评估",
                    "analysis_level": 4,
                    "debate_rounds": 2,
                    "risk_discussion_rounds": 2,
                    "debate_timeout": 300,
                    "risk_timeout": 120,
                    "enable_sentiment": True,
                    "enable_risk_assessment": True,
                    "is_system": True,
                    "is_default": False
                },
                {
                    "name": "全面分析",
                    "description": "全面分析，最大深度分析",
                    "analysis_level": 5,
                    "debate_rounds": 3,
                    "risk_discussion_rounds": 3,
                    "debate_timeout": 300,
                    "risk_timeout": 120,
                    "enable_sentiment": True,
                    "enable_risk_assessment": True,
                    "is_system": True,
                    "is_default": False
                }
            ]
            
            for preset in presets:
                existing = self.collection.find_one({
                    "name": preset["name"],
                    "is_system": True
                })
                if not existing:
                    current_time = datetime.now().isoformat()
                    preset["created_at"] = current_time
                    preset["updated_at"] = current_time
                    preset["user_id"] = "system"
                    self.collection.insert_one(preset)
                    logger.info(f"✅ 初始化系统预设: {preset['name']}")
                elif existing.get("analysis_level") is None:
                    self.collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"analysis_level": preset["analysis_level"]}}
                    )
                    logger.info(f"🔧 修复系统预设 {preset['name']} 的 analysis_level: {preset['analysis_level']}")
                else:
                    logger.info(f"ℹ️ 系统预设已存在: {preset['name']}")
            
            logger.info(f"✅ 成功初始化系统预设流程配置")
            return True
        except Exception as e:
            logger.error(f"[X] 初始化系统预设流程配置失败: {e}")
            return False
