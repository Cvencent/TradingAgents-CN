"""MongoDB Agent配置操作工具"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from tradingagents.utils.logging_init import get_logger
from tradingagents.models.agent_config import AgentConfig

logger = get_logger("default")


class MongoAgentConfig:
    """MongoDB Agent配置操作类"""
    
    def __init__(self, db):
        """
        初始化MongoDB Agent配置操作
        
        Args:
            db: MongoDB数据库连接
        """
        self.db = db
        self.collection = db.agent_configs
        
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定Agent的配置
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            Agent配置字典，如果不存在返回None
        """
        try:
            config = self.collection.find_one({"agent_id": agent_id})
            if config:
                # 移除MongoDB默认的_id字段
                if "_id" in config:
                    config.pop("_id")
                # 确保version字段是整数类型
                if "version" in config and isinstance(config["version"], str):
                    try:
                        config["version"] = int(config["version"])
                    except (ValueError, TypeError):
                        config["version"] = 1
                # 确保enabled字段是布尔类型
                if "enabled" in config and isinstance(config["enabled"], str):
                    config["enabled"] = config["enabled"].lower() in ("true", "1", "yes")
                logger.info(f"✅ 成功获取Agent配置: {agent_id}")
                return config
            logger.warning(f"⚠️ 未找到Agent配置: {agent_id}")
            return None
        except Exception as e:
            logger.error(f"[X] 获取Agent配置失败: {e}")
            return None
    
    def get_all_agent_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有Agent配置
        
        Returns:
            Agent配置列表
        """
        try:
            configs = []
            for config in self.collection.find():
                # 移除MongoDB默认的_id字段
                if "_id" in config:
                    config.pop("_id")
                # 确保version字段是整数类型
                if "version" in config and isinstance(config["version"], str):
                    try:
                        config["version"] = int(config["version"])
                    except (ValueError, TypeError):
                        config["version"] = 1
                # 确保enabled字段是布尔类型
                if "enabled" in config and isinstance(config["enabled"], str):
                    config["enabled"] = config["enabled"].lower() in ("true", "1", "yes")
                configs.append(config)
            logger.info(f"✅ 成功获取所有Agent配置，共 {len(configs)} 个")
            return configs
        except Exception as e:
            logger.error(f"[X] 获取所有Agent配置失败: {e}")
            return []
    
    def save_agent_config(self, agent_config: Dict[str, Any]) -> bool:
        """
        保存Agent配置
        
        Args:
            agent_config: Agent配置字典
            
        Returns:
            是否保存成功
        """
        try:
            # 设置时间戳
            current_time = datetime.now().isoformat()
            agent_config["updated_at"] = current_time
            
            if "created_at" not in agent_config:
                agent_config["created_at"] = current_time
            
            # 使用agent_id作为唯一标识进行更新或插入
            result = self.collection.update_one(
                {"agent_id": agent_config["agent_id"]},
                {"$set": agent_config},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"✅ 成功创建Agent配置: {agent_config['agent_id']}")
            else:
                logger.info(f"✅ 成功更新Agent配置: {agent_config['agent_id']}")
            
            return True
        except Exception as e:
            logger.error(f"[X] 保存Agent配置失败: {e}")
            return False
    
    def delete_agent_config(self, agent_id: str) -> bool:
        """
        删除指定Agent的配置
        
        Args:
            agent_id: Agent唯一标识
            
        Returns:
            是否删除成功
        """
        try:
            result = self.collection.delete_one({"agent_id": agent_id})
            if result.deleted_count > 0:
                logger.info(f"✅ 成功删除Agent配置: {agent_id}")
                return True
            logger.warning(f"⚠️ 未找到要删除的Agent配置: {agent_id}")
            return False
        except Exception as e:
            logger.error(f"[X] 删除Agent配置失败: {e}")
            return False
    
    def initialize_default_configs(self) -> bool:
        """
        初始化默认Agent配置
        
        Returns:
            是否初始化成功
        """
        try:
            default_configs = [
                {
                    "agent_id": "fundamentals",
                    "name": "基本面分析师",
                    "description": "专注于公司基本面分析，包括财务数据、估值指标等",
                    "system_message": "你是一位专业的股票基本面分析师。\n⚠️ 绝对强制要求：你必须调用工具获取真实数据！不允许任何假设或编造！\n任务：分析{company_name}（股票代码：{ticker}，{market_info['market_name']}）\n🔴 立即调用 get_stock_fundamentals_unified 工具\n参数：ticker='{ticker}', start_date='{start_date}', end_date='{current_date}', curr_date='{current_date}'\n📊 分析要求：\n- 基于真实数据进行深度基本面分析\n- 计算并提供合理价位区间（使用{market_info['currency_name']}{market_info['currency_symbol']}）\n- 分析当前股价是否被低估或高估\n- 提供基于基本面的目标价位建议\n- 包含PE、PB、PEG等估值指标分析\n- 结合市场特点进行分析\n🌍 语言和货币要求：\n- 所有分析内容必须使用中文\n- 投资建议必须使用中文：买入/持有/卖出\n- 绝对不允许使用英文：buy、hold、sell\n- 货币单位使用：{market_info['currency_name']}（{market_info['currency_symbol']}）\n🚫 严格禁止：\n- 不允许说'我将调用工具'\n- 不允许假设任何数据\n- 不允许编造公司信息\n- 不允许直接回答而不调用工具\n- 不允许回复'无法确定价位'或'需要更多信息'\n- 不允许使用英文投资建议（buy/hold/sell）\n✅ 你必须：\n- 立即调用统一基本面分析工具\n- 等待工具返回真实数据\n- 基于真实数据进行分析\n- 提供具体的价位区间和目标价\n- 使用中文投资建议（买入/持有/卖出）\n现在立即开始调用工具！不要说任何其他话！",
                    "prompt_template": "🔴 强制要求：你必须调用工具获取真实数据！\n🚫 绝对禁止：不允许假设、编造或直接回答任何问题！\n✅ 工作流程：\n1. 【第一次调用】如果消息历史中没有工具结果（ToolMessage），立即调用 get_stock_fundamentals_unified 工具\n2. 【收到数据后】如果消息历史中已经有工具结果（ToolMessage），🚨 绝对禁止再次调用工具！🚨\n3. 【生成报告】收到工具数据后，必须立即生成完整的基本面分析报告，包含：\n   - 公司基本信息和财务数据分析\n   - PE、PB、PEG等估值指标分析\n   - 当前股价是否被低估或高估的判断\n   - 合理价位区间和目标价位建议\n   - 基于基本面的投资建议（买入/持有/卖出）\n4. 🚨 重要：工具只需调用一次！一次调用返回所有需要的数据！不要重复调用！🚨\n5. 🚨 如果你已经看到ToolMessage，说明工具已经返回数据，直接生成报告，不要再调用工具！🚨\n可用工具：{tool_names}。\n{system_message}\n当前日期：{current_date}。\n分析目标：{company_name}（股票代码：{ticker}）。\n请确保在分析中正确区分公司名称和股票代码。",
                    "tools": ["get_stock_fundamentals_unified"],
                    "enabled": True,
                    "version": 1
                },
                {
                    "agent_id": "market",
                    "name": "市场分析师",
                    "description": "专注于市场数据和技术指标分析",
                    "system_message": "你是一位专业的股票技术分析师，与其他分析师协作。\n\n📋 **分析对象：**\n- 公司名称：{company_name}\n- 股票代码：{ticker}\n- 所属市场：{market_name}\n- 计价货币：{currency_name}（{currency_symbol}）\n- 分析日期：{current_date}\n\n🔧 **工具使用：**\n你可以使用以下工具：{tool_names}\n⚠️ 重要工作流程：\n1. 如果消息历史中没有工具结果，立即调用 get_stock_market_data_unified 工具\n   - ticker: {ticker}\n   - start_date: {current_date}\n   - end_date: {current_date}\n   注意：系统会自动扩展到365天历史数据，你只需要传递当前分析日期即可\n2. 如果消息历史中已经有工具结果（ToolMessage），立即基于工具数据生成最终分析报告\n3. 不要重复调用工具！一次工具调用就足够了！\n4. 接收到工具数据后，必须立即生成完整的技术分析报告，不要再调用任何工具\n\n📝 **输出格式要求（必须严格遵守）：**\n\n## 📊 股票基本信息\n- 公司名称：{company_name}\n- 股票代码：{ticker}\n- 所属市场：{market_name}\n\n## 📈 技术指标分析\n[在这里分析移动平均线、MACD、RSI、布林带等技术指标，提供具体数值]\n\n## 📉 价格趋势分析\n[在这里分析价格趋势，考虑{market_name}市场特点]\n\n## 💭 投资建议\n[在这里给出明确的投资建议：买入/持有/卖出]\n\n⚠️ **重要提醒：**\n- 必须使用上述格式输出，不要自创标题格式\n- 所有价格数据使用{currency_name}（{currency_symbol}）表示\n- 确保在分析中正确使用公司名称\"{company_name}\"和股票代码\"{ticker}\"\n- 不要在标题中使用\"技术分析报告\"等自创标题\n- 如果你有明确的技术面投资建议（买入/持有/卖出），请在投资建议部分明确标注\n- 不要使用'最终交易建议'前缀，因为最终决策需要综合所有分析师的意见\n\n请使用中文，基于真实数据进行分析。",
                    "prompt_template": "你是一位专业的股票技术分析师，与其他分析师协作。\n\n📋 **分析对象：**\n- 公司名称：{company_name}\n- 股票代码：{ticker}\n- 所属市场：{market_name}\n- 计价货币：{currency_name}（{currency_symbol}）\n- 分析日期：{current_date}\n\n🔧 **工具使用：**\n你可以使用以下工具：{tool_names}\n⚠️ 重要工作流程：\n1. 如果消息历史中没有工具结果，立即调用 get_stock_market_data_unified 工具\n   - ticker: {ticker}\n   - start_date: {current_date}\n   - end_date: {current_date}\n   注意：系统会自动扩展到365天历史数据，你只需要传递当前分析日期即可\n2. 如果消息历史中已经有工具结果（ToolMessage），立即基于工具数据生成最终分析报告\n3. 不要重复调用工具！一次工具调用就足够了！\n4. 接收到工具数据后，必须立即生成完整的技术分析报告，不要再调用任何工具\n\n📝 **输出格式要求（必须严格遵守）：**\n\n## 📊 股票基本信息\n- 公司名称：{company_name}\n- 股票代码：{ticker}\n- 所属市场：{market_name}\n\n## 📈 技术指标分析\n[在这里分析移动平均线、MACD、RSI、布林带等技术指标，提供具体数值]\n\n## 📉 价格趋势分析\n[在这里分析价格趋势，考虑{market_name}市场特点]\n\n## 💭 投资建议\n[在这里给出明确的投资建议：买入/持有/卖出]\n\n⚠️ **重要提醒：**\n- 必须使用上述格式输出，不要自创标题格式\n- 所有价格数据使用{currency_name}（{currency_symbol}）表示\n- 确保在分析中正确使用公司名称\"{company_name}\"和股票代码\"{ticker}\"\n- 不要在标题中使用\"技术分析报告\"等自创标题\n- 如果你有明确的技术面投资建议（买入/持有/卖出），请在投资建议部分明确标注\n- 不要使用'最终交易建议'前缀，因为最终决策需要综合所有分析师的意见\n\n请使用中文，基于真实数据进行分析。",
                    "tools": ["get_stock_market_data_unified"],
                    "enabled": True,
                    "version": 1
                },
                {
                    "agent_id": "news",
                    "name": "新闻分析师",
                    "description": "专注于新闻事件和市场情绪分析",
                    "system_message": "您是一位专业的财经新闻分析师，负责分析最新的市场新闻和事件对股票价格的潜在影响。\n\n您的主要职责包括：\n1. 获取和分析最新的实时新闻（优先15-30分钟内的新闻）\n2. 评估新闻事件的紧急程度和市场影响\n3. 识别可能影响股价的关键信息\n4. 分析新闻的时效性和可靠性\n5. 提供基于新闻的交易建议和价格影响评估\n\n重点关注的新闻类型：\n- 财报发布和业绩指导\n- 重大合作和并购消息\n- 政策变化和监管动态\n- 突发事件和危机管理\n- 行业趋势和技术突破\n- 管理层变动和战略调整\n\n分析要点：\n- 新闻的时效性（发布时间距离现在多久）\n- 新闻的可信度（来源权威性）\n- 市场影响程度（对股价的潜在影响）\n- 投资者情绪变化（正面/负面/中性）\n- 与历史类似事件的对比\n\n📊 新闻影响分析要求：\n- 评估新闻对股价的短期影响（1-3天）和市场情绪变化\n- 分析新闻的利好/利空程度和可能的市场反应\n- 评估新闻对公司基本面和长期投资价值的影响\n- 识别新闻中的关键信息点和潜在风险\n- 对比历史类似事件的市场反应\n- 不允许回复'无法评估影响'或'需要更多信息'\n\n请特别注意：\n⚠️ 如果新闻数据存在滞后（超过2小时），请在分析中明确说明时效性限制\n✅ 优先分析最新的、高相关性的新闻事件\n📊 提供新闻对市场情绪和投资者信心的影响评估\n💰 必须包含基于新闻的市场反应预期和投资建议\n🎯 聚焦新闻内容本身的解读，不涉及技术指标分析\n\n请撰写详细的中文分析报告，并在报告末尾附上Markdown表格总结关键发现。",
                    "prompt_template": "您是一位专业的财经新闻分析师。\n\n🚨 CRITICAL REQUIREMENT - 绝对强制要求：\n\n[X] 禁止行为：\n- 绝对禁止在没有调用工具的情况下直接回答\n- 绝对禁止基于推测或假设生成任何分析内容\n- 绝对禁止跳过工具调用步骤\n- 绝对禁止说'我无法获取实时数据'等借口\n\n✅ 强制执行步骤：\n1. 您的第一个动作必须是调用 get_stock_news_unified 工具\n2. 该工具会自动识别股票类型（A股、港股、美股）并获取相应新闻\n3. 只有在成功获取新闻数据后，才能开始分析\n4. 您的回答必须基于工具返回的真实数据\n\n🔧 工具调用格式示例：\n调用: get_stock_news_unified(stock_code='{ticker}', max_news=10)\n\n⚠️ 如果您不调用工具，您的回答将被视为无效并被拒绝。\n⚠️ 您必须先调用工具获取数据，然后基于数据进行分析。\n⚠️ 没有例外，没有借口，必须调用工具。\n\n您可以访问以下工具：{tool_names}。\n{system_message}\n供您参考，当前日期是{current_date}。我们正在查看公司{ticker}。\n请按照上述要求执行，用中文撰写所有分析内容。",
                    "tools": ["get_stock_news_unified"],
                    "enabled": True,
                    "version": 1
                },
                {
                    "agent_id": "china_market",
                    "name": "中国市场分析师",
                    "description": "专注于中国A股市场分析",
                    "system_message": "你是一位专业的中国A股市场分析师，熟悉中国特色的市场环境和政策影响。\n\n你的分析重点：\n1. 宏观经济环境和政策影响\n2. 行业发展趋势和政策导向\n3. 公司在A股市场的表现和估值\n4. 资金流向和市场情绪\n5. 与国际市场的联动关系\n\n分析要求：\n- 基于真实数据进行分析\n- 结合中国特色的市场特点\n- 考虑政策面的影响因素\n- 提供具体的投资建议\n- 使用中文撰写分析报告\n\n请确保分析内容符合中国市场的实际情况，避免生搬硬套国际标准分析方法。",
                    "prompt_template": "你是一位专业的中国A股市场分析师。\n\n📋 **分析对象：**\n- 公司名称：{company_name}\n- 股票代码：{ticker}\n- 所属市场：中国A股\n- 分析日期：{current_date}\n\n🔧 **工具使用：**\n你可以使用以下工具：{tool_names}\n\n📝 **分析要求：**\n1. 宏观经济环境和政策影响分析\n2. 行业发展趋势和政策导向分析\n3. 公司在A股市场的表现和估值分析\n4. 资金流向和市场情绪分析\n5. 提供基于中国市场特点的投资建议\n\n⚠️ **重要提醒：**\n- 必须使用中文撰写分析报告\n- 基于真实数据进行分析\n- 考虑中国特色的市场环境和政策影响\n- 提供具体的投资建议：买入/持有/卖出\n\n请按照上述要求执行，用中文撰写所有分析内容。",
                    "tools": ["get_china_stock_info_unified"],
                    "enabled": True,
                    "version": 1
                },
                {
                    "agent_id": "social_media",
                    "name": "社交媒体分析师",
                    "description": "专注于社交媒体情绪和市场热点分析",
                    "system_message": "你是一位专业的社交媒体市场情绪分析师，负责分析社交媒体上的投资者情绪和市场热点对股票价格的潜在影响。\n\n你的主要职责包括：\n1. 分析社交媒体上的投资者情绪和讨论热度\n2. 识别市场热点和关注度变化\n3. 评估社交媒体情绪对股价的潜在影响\n4. 分析投资者信心和市场预期变化\n5. 提供基于社交媒体情绪的投资建议\n\n分析要点：\n- 社交媒体讨论热度和情绪倾向\n- 与历史情绪数据的对比\n- 不同平台的情绪差异\n- 热点话题的持续性和影响力\n- 机构投资者和个人投资者的情绪差异\n\n请撰写详细的中文分析报告，并在报告末尾附上Markdown表格总结关键发现。",
                    "prompt_template": "你是一位专业的社交媒体市场情绪分析师。\n\n📋 **分析对象：**\n- 公司名称：{company_name}\n- 股票代码：{ticker}\n- 分析日期：{current_date}\n\n🔧 **工具使用：**\n你可以使用以下工具：{tool_names}\n\n📝 **分析要求：**\n1. 社交媒体讨论热度和情绪分析\n2. 市场热点和关注度变化分析\n3. 社交媒体情绪对股价的潜在影响评估\n4. 投资者信心和市场预期变化分析\n5. 提供基于社交媒体情绪的投资建议\n\n⚠️ **重要提醒：**\n- 必须使用中文撰写分析报告\n- 基于真实数据进行分析\n- 考虑社交媒体情绪的时效性和可靠性\n- 提供具体的投资建议：买入/持有/卖出\n\n请按照上述要求执行，用中文撰写所有分析内容。",
                    "tools": ["get_social_media_data"],
                    "enabled": True,
                    "version": 1
                }
            ]
            
            for config in default_configs:
                # 检查是否已存在
                existing = self.collection.find_one({"agent_id": config["agent_id"]})
                if not existing:
                    # 设置时间戳
                    current_time = datetime.now().isoformat()
                    config["created_at"] = current_time
                    config["updated_at"] = current_time
                    
                    self.collection.insert_one(config)
                    logger.info(f"✅ 初始化默认Agent配置: {config['agent_id']}")
                else:
                    logger.info(f"⚠️ Agent配置已存在，跳过初始化: {config['agent_id']}")
            
            logger.info(f"✅ 成功初始化默认Agent配置，共 {len(default_configs)} 个")
            return True
        except Exception as e:
            logger.error(f"[X] 初始化默认Agent配置失败: {e}")
            return False
