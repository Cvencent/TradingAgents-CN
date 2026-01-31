"""Agent配置管理工具"""

from typing import Dict, Optional, Any
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.mongo_agent_config import MongoAgentConfig
from tradingagents.models.agent_config import AgentConfig

logger = get_logger("default")


class AgentConfigManager:
    """Agent配置管理类"""
    
    _instance = None
    
    def __new__(cls, db=None):
        """单例模式"""
        if not cls._instance and db:
            cls._instance = super(AgentConfigManager, cls).__new__(cls)
            cls._instance._init(db)
        return cls._instance
    
    def _init(self, db):
        """初始化"""
        self.db = db
        self.mongo_config = MongoAgentConfig(db)
        self._config_cache = {}
        logger.info("✅ Agent配置管理器初始化成功")
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定Agent的配置
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            Agent配置字典，如果不存在返回None
        """
        try:
            # 先从缓存获取
            if agent_id in self._config_cache:
                logger.debug(f"🔄 从缓存获取Agent配置: {agent_id}")
                return self._config_cache[agent_id]
            
            # 从MongoDB获取
            config = self.mongo_config.get_agent_config(agent_id)
            if config:
                # 存入缓存
                self._config_cache[agent_id] = config
                logger.info(f"✅ 成功获取Agent配置: {agent_id}")
            else:
                logger.warning(f"⚠️ 未找到Agent配置: {agent_id}")
            
            return config
        except Exception as e:
            logger.error(f"❌ 获取Agent配置失败: {e}")
            return None
    
    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()
        logger.info("✅ Agent配置缓存已清除")
    
    def get_system_message(self, agent_id: str) -> Optional[str]:
        """
        获取指定Agent的系统消息
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            系统消息字符串，如果不存在返回None
        """
        config = self.get_agent_config(agent_id)
        return config.get("system_message") if config else None
    
    def get_prompt_template(self, agent_id: str) -> Optional[str]:
        """
        获取指定Agent的提示模板
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            提示模板字符串，如果不存在返回None
        """
        config = self.get_agent_config(agent_id)
        return config.get("prompt_template") if config else None
    
    def get_tools(self, agent_id: str) -> list:
        """
        获取指定Agent的工具列表
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            工具列表，如果不存在返回空列表
        """
        config = self.get_agent_config(agent_id)
        return config.get("tools", []) if config else []
    
    def is_enabled(self, agent_id: str) -> bool:
        """
        检查指定Agent是否启用
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            是否启用
        """
        config = self.get_agent_config(agent_id)
        return config.get("enabled", True) if config else True


# 全局实例
agent_config_manager = None


def init_agent_config_manager(db):
    """
    初始化Agent配置管理器
    
    Args:
        db: MongoDB数据库连接
    """
    global agent_config_manager
    agent_config_manager = AgentConfigManager(db)
    return agent_config_manager


def get_agent_config_manager() -> Optional[AgentConfigManager]:
    """
    获取全局Agent配置管理器实例
    
    Returns:
        Agent配置管理器实例
    """
    global agent_config_manager
    return agent_config_manager
