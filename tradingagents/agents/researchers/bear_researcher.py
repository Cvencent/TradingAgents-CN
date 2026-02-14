from langchain_core.messages import AIMessage
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        # 使用统一的股票类型检测
        ticker = state.get('company_of_interest', 'Unknown')
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)
        is_china = market_info['is_china']

        # 获取公司名称
        def _get_company_name(ticker_code: str, market_info_dict: dict) -> str:
            """根据股票代码获取公司名称"""
            try:
                if market_info_dict['is_china']:
                    from tradingagents.dataflows.interface import get_china_stock_info_unified
                    stock_info = get_china_stock_info_unified(ticker_code)
                    if stock_info and "股票名称:" in stock_info:
                        name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                        logger.info(f"✅ [空头研究员] 成功获取中国股票名称: {ticker_code} -> {name}")
                        return name
                    else:
                        # 降级方案
                        try:
                            from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                            info_dict = get_info_dict(ticker_code)
                            if info_dict and info_dict.get('name'):
                                name = info_dict['name']
                                logger.info(f"✅ [空头研究员] 降级方案成功获取股票名称: {ticker_code} -> {name}")
                                return name
                        except Exception as e:
                            logger.error(f"[X] [空头研究员] 降级方案也失败: {e}")
                elif market_info_dict['is_hk']:
                    try:
                        from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                        name = get_hk_company_name_improved(ticker_code)
                        return name
                    except Exception:
                        clean_ticker = ticker_code.replace('.HK', '').replace('.hk', '')
                        return f"港股{clean_ticker}"
                elif market_info_dict['is_us']:
                    us_stock_names = {
                        'AAPL': '苹果公司', 'TSLA': '特斯拉', 'NVDA': '英伟达',
                        'MSFT': '微软', 'GOOGL': '谷歌', 'AMZN': '亚马逊',
                        'META': 'Meta', 'NFLX': '奈飞'
                    }
                    return us_stock_names.get(ticker_code.upper(), f"美股{ticker_code}")
            except Exception as e:
                logger.error(f"[X] [空头研究员] 获取公司名称失败: {e}")
            return f"股票代码{ticker_code}"

        company_name = _get_company_name(ticker, market_info)
        is_hk = market_info['is_hk']
        is_us = market_info['is_us']

        currency = market_info['currency_name']
        currency_symbol = market_info['currency_symbol']

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        # 安全检查：确保memory不为None
        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""你是一位看跌分析师，负责论证不投资股票 {company_name}（股票代码：{ticker}）的理由。

⚠️ 重要提醒：当前分析的是 {market_info['market_name']}，所有价格和估值请使用 {currency}（{currency_symbol}）作为单位。
⚠️ 在你的分析中，请始终使用公司名称"{company_name}"而不是股票代码"{ticker}"来称呼这家公司。

你的目标是提出合理的论证，强调风险、挑战和负面指标。利用提供的研究和数据来突出潜在的不利因素并有效反驳看涨论点。

请用中文回答，重点关注以下几个方面：

- 风险和挑战：突出市场饱和、财务不稳定或宏观经济威胁等可能阻碍股票表现的因素
- 竞争劣势：强调市场地位较弱、创新下降或来自竞争对手威胁等脆弱性
- 负面指标：使用财务数据、市场趋势或最近不利消息的证据来支持你的立场
- 反驳看涨观点：用具体数据和合理推理批判性分析看涨论点，揭露弱点或过度乐观的假设
- 参与讨论：以对话风格呈现你的论点，直接回应看涨分析师的观点并进行有效辩论，而不仅仅是列举事实

可用资源：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务新闻：{news_report}
公司基本面报告：{fundamentals_report}
辩论对话历史：{history}
最后的看涨论点：{current_response}
类似情况的反思和经验教训：{past_memory_str}

请使用这些信息提供令人信服的看跌论点，反驳看涨声明，并参与动态辩论，展示投资该股票的风险和弱点。你还必须处理反思并从过去的经验教训和错误中学习。

请确保所有回答都使用中文。
"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_count = investment_debate_state["count"] + 1
        logger.info(f"🐻 [空头研究员] 发言完成，计数: {investment_debate_state['count']} -> {new_count}")

        # 兼容旧格式（字符串）和新格式（列表）
        current_bear_history = investment_debate_state.get("bear_history", "")
        if isinstance(current_bear_history, list):
            # 新格式：列表，追加当前轮次
            new_bear_history = current_bear_history + [argument]
        else:
            # 旧格式：字符串，转换为列表并追加
            if current_bear_history:
                new_bear_history = [current_bear_history, argument]
            else:
                new_bear_history = [argument]

        # 🔧 保存当前prompt到bear_prompts列表（用于前端展示）
        current_bear_prompts = investment_debate_state.get("bear_prompts", [])
        if not isinstance(current_bear_prompts, list):
            current_bear_prompts = []
        new_bear_prompts = current_bear_prompts + [prompt]
        logger.info(f"🔍 [Bear Researcher] 保存prompt到bear_prompts，当前轮数: {len(new_bear_prompts)}, prompt长度: {len(prompt)} chars")

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": new_bear_history,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": new_count,
            "bear_prompts": new_bear_prompts,  # 🔧 保存prompts
        }

        logger.info(f"🔍 [Bear Researcher] 返回investment_debate_state，包含字段: {list(new_investment_debate_state.keys())}")
        
        # 🔥 关键修复：同时返回 bear_request_prompt 字段（用于前端展示原始prompt）
        # 将所有轮次的prompt合并，用分隔符隔开
        full_bear_prompt = "\n\n" + "="*60 + "\n【空头研究员 - 多轮辩论Prompts】\n" + "="*60 + "\n\n"
        for i, p in enumerate(new_bear_prompts, 1):
            full_bear_prompt += f"\n--- 第 {i} 轮 ---\n{p}\n"
        
        logger.info(f"🔍 [Bear Researcher] 返回 bear_request_prompt，总长度: {len(full_bear_prompt)} chars")
        return {
            "investment_debate_state": new_investment_debate_state,
            "bear_request_prompt": full_bear_prompt  # 🔥 保存完整的请求prompt
        }

    return bear_node
