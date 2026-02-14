from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
import traceback
import re

# 导入分析模块日志装饰器
from tradingagents.utils.tool_logging import log_analyst_module

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")

# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler

# 导入LLM链创建工具
from tradingagents.agents.utils.llm_chain_utils import (
    create_llm_chain,
    should_use_tool_call_handler,
    log_model_usage
)

# 导入Agent配置管理器
from tradingagents.agents.utils.agent_config_manager import get_agent_config_manager


def _get_company_name(ticker: str, market_info: dict) -> str:
    """
    根据股票代码获取公司名称

    Args:
        ticker: 股票代码
        market_info: 市场信息字典

    Returns:
        str: 公司名称
    """
    try:
        if market_info['is_china']:
            # 中国A股：使用统一接口获取股票信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)

            logger.debug(f"📊 [技术面分析师] 获取股票信息返回: {stock_info[:200] if stock_info else 'None'}...")

            # 解析股票名称
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [技术面分析师] 成功获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                # 降级方案：尝试直接从数据源管理器获取
                logger.warning(f"⚠️ [技术面分析师] 无法从统一接口解析股票名称: {ticker}，尝试降级方案")
                try:
                    from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                    info_dict = get_info_dict(ticker)
                    if info_dict and info_dict.get('name'):
                        company_name = info_dict['name']
                        logger.info(f"✅ [技术面分析师] 降级方案成功获取股票名称: {ticker} -> {company_name}")
                        return company_name
                except Exception as e:
                    logger.error(f"[X] [技术面分析师] 降级方案也失败: {e}")

                logger.error(f"[X] [技术面分析师] 所有方案都无法获取股票名称: {ticker}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"📊 [DEBUG] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"📊 [DEBUG] 改进港股工具获取名称失败: {e}")
                # 降级方案：生成友好的默认名称
                clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                return f"港股{clean_ticker}"

        elif market_info['is_us']:
            # 美股：使用简单映射或返回代码
            us_stock_names = {
                'AAPL': '苹果公司',
                'TSLA': '特斯拉',
                'NVDA': '英伟达',
                'MSFT': '微软',
                'GOOGL': '谷歌',
                'AMZN': '亚马逊',
                'META': 'Meta',
                'NFLX': '奈飞'
            }

            company_name = us_stock_names.get(ticker.upper(), f"美股{ticker}")
            logger.debug(f"📊 [DEBUG] 美股名称映射: {ticker} -> {company_name}")
            return company_name

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"[X] [DEBUG] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_market_analyst(llm, toolkit):

    def market_analyst_node(state):
        logger.debug(f"📈 [DEBUG] ===== 技术面分析师节点开始 =====")

        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("market_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        logger.debug(f"📈 [DEBUG] 输入参数: ticker={ticker}, date={current_date}")
        logger.debug(f"📈 [DEBUG] 当前状态中的消息数量: {len(state.get('messages', []))}")
        logger.debug(f"📈 [DEBUG] 现有市场报告: {state.get('market_report', 'None')}")

        # 根据股票代码格式选择数据源
        from tradingagents.utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)

        logger.debug(f"📈 [DEBUG] 股票类型检查: {ticker} -> {market_info['market_name']} ({market_info['currency_name']})")

        # 获取公司名称
        company_name = _get_company_name(ticker, market_info)
        logger.debug(f"📈 [DEBUG] 公司名称: {ticker} -> {company_name}")

        # 统一使用 get_stock_market_data_unified 工具
        # 该工具内部会自动识别股票类型（A股/港股/美股）并调用相应的数据源
        logger.info(f"📊 [技术面分析师] 使用统一市场数据工具，自动识别股票类型")
        tools = [toolkit.get_stock_market_data_unified]

        # 安全地获取工具名称用于调试
        tool_names_debug = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names_debug.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names_debug.append(tool.__name__)
            else:
                tool_names_debug.append(str(tool))
        logger.info(f"📊 [技术面分析师] 绑定的工具: {tool_names_debug}")
        logger.info(f"📊 [技术面分析师] 目标市场: {market_info['market_name']}")

        # 从MongoDB获取配置，如果不存在则使用默认配置
        config_manager = get_agent_config_manager()
        
        # 默认提示模板
        default_system_prompt = """你是一位专业的股票技术分析师，与其他分析师协作。

📋 **分析对象：**
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_name}
- 计价货币：{currency_name}（{currency_symbol}）
- 分析日期：{current_date}

🔧 **工具使用：**
你可以使用以下工具：{tool_names}
⚠️ 重要工作流程：
1. 如果消息历史中没有工具结果，立即调用 get_stock_market_data_unified 工具
   - ticker: {ticker}
   - start_date: {current_date}
   - end_date: {current_date}
   注意：系统会自动扩展到365天历史数据，你只需要传递当前分析日期即可
2. 如果消息历史中已经有工具结果（ToolMessage），立即基于工具数据生成最终分析报告
3. 不要重复调用工具！一次工具调用就足够了！
4. 接收到工具数据后，必须立即生成完整的技术分析报告，不要再调用任何工具

📝 **输出格式要求（必须严格遵守）：**

## 📊 股票基本信息
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_name}

## 📈 技术指标分析
[在这里分析移动平均线、MACD、RSI、布林带等技术指标，提供具体数值]

## 📉 价格趋势分析
[在这里分析价格趋势，考虑{market_name}市场特点]

## 💭 投资建议
[在这里给出明确的投资建议：买入/持有/卖出]

⚠️ **重要提醒：**
- 必须使用上述格式输出，不要自创标题格式
- 所有价格数据使用{currency_name}（{currency_symbol}）表示
- 确保在分析中正确使用公司名称"{company_name}"和股票代码"{ticker}"
- 不要在标题中使用"技术分析报告"等自创标题
- 如果你有明确的技术面投资建议（买入/持有/卖出），请在投资建议部分明确标注
- 不要使用'最终交易建议'前缀，因为最终决策需要综合所有分析师的意见

请使用中文，基于真实数据进行分析。"""
        
        # 从配置管理器获取配置
        system_prompt = default_system_prompt
        
        if config_manager:
            # 尝试从MongoDB获取提示模板
            db_prompt_template = config_manager.get_prompt_template("market")
            if db_prompt_template:
                system_prompt = db_prompt_template
                logger.info("✅ 从MongoDB加载提示模板成功")
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # 安全地获取工具名称，处理函数和工具对象
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))

        # 🔥 设置所有模板变量
        prompt = prompt.partial(tool_names=", ".join(tool_names))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(company_name=company_name)
        prompt = prompt.partial(market_name=market_info['market_name'])
        prompt = prompt.partial(currency_name=market_info['currency_name'])
        prompt = prompt.partial(currency_symbol=market_info['currency_symbol'])

        # 添加详细日志
        logger.info(f"📊 [技术面分析师] LLM类型: {llm.__class__.__name__}")
        logger.info(f"📊 [技术面分析师] LLM模型: {getattr(llm, 'model_name', 'unknown')}")
        logger.info(f"📊 [技术面分析师] 消息历史数量: {len(state['messages'])}")
        logger.info(f"📊 [技术面分析师] 公司名称: {company_name}")
        logger.info(f"📊 [技术面分析师] 股票代码: {ticker}")

        # 打印提示词模板信息
        logger.info("📊 [技术面分析师] ========== 提示词模板信息 ==========")
        logger.info(f"📊 [技术面分析师] 模板变量已设置: company_name={company_name}, ticker={ticker}, market={market_info['market_name']}")
        logger.info("📊 [技术面分析师] ==========================================")

        # 打印实际传递给LLM的消息
        logger.info(f"📊 [技术面分析师] ========== 传递给LLM的消息 ==========")
        for i, msg in enumerate(state["messages"]):
            msg_type = type(msg).__name__
            # 🔥 修复：更安全地提取消息内容
            if hasattr(msg, 'content'):
                msg_content = str(msg.content)[:500]  # 增加到500字符以便查看完整内容
            elif isinstance(msg, tuple) and len(msg) >= 2:
                # 处理旧格式的元组消息 ("human", "content")
                msg_content = f"[元组消息] 类型={msg[0]}, 内容={str(msg[1])[:500]}"
            else:
                msg_content = str(msg)[:500]
            logger.info(f"📊 [技术面分析师] 消息[{i}] 类型={msg_type}, 内容={msg_content}")
        logger.info(f"📊 [技术面分析师] ========== 消息列表结束 ==========")

        # 使用统一的LLM链创建工具（支持DeepSeek/302AI等模型）
        log_model_usage(llm, "技术面分析师")
        chain = create_llm_chain(
            prompt=prompt,
            llm=llm,
            tools=tools,
            bind_tools=True,
            analyst_name="技术面分析师"
        )

        # 🔧 调试：检查当前 state 中是否已有报告
        existing_report = state.get("market_report", "")
        tool_call_count = state.get("market_tool_call_count", 0)
        logger.info(f"📊 [技术面分析师] 节点开始执行:")
        logger.info(f"  - 现有报告长度: {len(existing_report) if existing_report else 0}")
        logger.info(f"  - 工具调用次数: {tool_call_count}")
        logger.info(f"  - 消息数量: {len(state.get('messages', []))}")
        
        # 🔥 构建完整的请求prompt（用于保存和前端展示）
        # 使用prompt.format_messages获取实际发送给LLM的完整消息
        try:
            formatted_messages = prompt.format_messages(messages=state["messages"])
            full_request_prompt = ""
            for msg in formatted_messages:
                msg_type = type(msg).__name__
                if hasattr(msg, 'content'):
                    full_request_prompt += f"\n\n=== {msg_type} ===\n{msg.content}"
            logger.info(f"📊 [技术面分析师] 构建完整请求prompt，长度: {len(full_request_prompt)}")
        except Exception as e:
            logger.warning(f"⚠️ [技术面分析师] 构建完整prompt失败: {e}")
            full_request_prompt = system_prompt  # 降级使用system_prompt
        
        logger.info(f"📊 [技术面分析师] 开始调用LLM...")
        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})
        logger.info(f"📊 [技术面分析师] LLM调用完成")

        # 打印LLM响应
        logger.info(f"📊 [技术面分析师] ========== LLM响应开始 ==========")
        logger.info(f"📊 [技术面分析师] 响应类型: {type(result).__name__}")
        logger.info(f"📊 [技术面分析师] 响应内容: {str(result.content)[:1000]}...")
        if hasattr(result, 'tool_calls') and result.tool_calls:
            logger.info(f"📊 [技术面分析师] 工具调用: {result.tool_calls}")
        logger.info(f"📊 [技术面分析师] ========== LLM响应结束 ==========")

        # 使用统一的Google工具调用处理器
        if should_use_tool_call_handler(llm):
            logger.info(f"📊 [技术面分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="市场分析",
                specific_requirements="重点关注市场数据、价格走势、交易量变化等市场指标。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="技术面分析师"
            )

            # 🔧 更新工具调用计数器
            # 🔥 构建包含AI回复的完整prompt
            full_prompt_with_response = full_request_prompt + "\n\n" + "="*60 + "\n【AI 回复】\n" + "="*60 + "\n"
            full_prompt_with_response += f"\n{report}\n"
            logger.info(f"📊 [技术面分析师] 准备返回结果:")
            logger.info(f"  - market_report长度: {len(report) if report else 0}")
            logger.info(f"  - market_request_prompt长度: {len(full_prompt_with_response) if full_prompt_with_response else 0}")
            logger.info(f"  - tool_call_count: {tool_call_count + 1}")
            
            return {
                "messages": [result],
                "market_report": report,
                "market_request_prompt": full_prompt_with_response,  # 🔥 保存包含AI回复的完整prompt
                "market_tool_call_count": tool_call_count + 1
            }
        else:
            # 🔥 关键修复：处理非Google模型的情况
            logger.info(f"📊 [技术面分析师] 非Google模型，直接处理结果")
            
            # 提取报告内容
            if hasattr(result, 'content'):
                report = str(result.content)
            else:
                report = str(result)
            
            # 🔧 更新工具调用计数器
            # 🔥 构建包含AI回复的完整prompt
            full_prompt_with_response = full_request_prompt + "\n\n" + "="*60 + "\n【AI 回复】\n" + "="*60 + "\n"
            full_prompt_with_response += f"\n{report}\n"
            logger.info(f"📊 [技术面分析师] 准备返回结果:")
            logger.info(f"  - market_report长度: {len(report) if report else 0}")
            logger.info(f"  - market_request_prompt长度: {len(full_prompt_with_response) if full_prompt_with_response else 0}")
            logger.info(f"  - tool_call_count: {tool_call_count + 1}")
            
            return {
                "messages": [result],
                "market_report": report,
                "market_request_prompt": full_prompt_with_response,  # 🔥 保存包含AI回复的完整prompt
                "market_tool_call_count": tool_call_count + 1
            }

    return market_analyst_node
