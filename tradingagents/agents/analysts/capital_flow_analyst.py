from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
import traceback

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


def _get_company_name_for_capital_flow(ticker: str, market_info: dict) -> str:
    """
    为资金盘分析师获取公司名称

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

            logger.debug(f"💰 [资金盘分析师] 获取股票信息返回: {stock_info[:200] if stock_info else 'None'}...")

            # 解析股票名称
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [资金盘分析师] 成功获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                # 降级方案：尝试直接从数据源管理器获取
                logger.warning(f"⚠️ [资金盘分析师] 无法从统一接口解析股票名称: {ticker}，尝试降级方案")
                try:
                    from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                    info_dict = get_info_dict(ticker)
                    if info_dict and info_dict.get('name'):
                        company_name = info_dict['name']
                        logger.info(f"✅ [资金盘分析师] 降级方案成功获取股票名称: {ticker} -> {company_name}")
                        return company_name
                except Exception as e:
                    logger.error(f"❌ [资金盘分析师] 降级方案也失败: {e}")

                logger.error(f"❌ [资金盘分析师] 所有方案都无法获取股票名称: {ticker}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"💰 [DEBUG] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"💰 [DEBUG] 改进港股工具获取名称失败: {e}")
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
            logger.debug(f"💰 [DEBUG] 美股名称映射: {ticker} -> {company_name}")
            return company_name

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"❌ [DEBUG] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_capital_flow_analyst(llm, toolkit):

    def capital_flow_analyst_node(state):
        logger.debug(f"💰 [DEBUG] ===== 资金盘分析师节点开始 =====")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        logger.debug(f"💰 [DEBUG] 输入参数: ticker={ticker}, date={current_date}")
        logger.debug(f"💰 [DEBUG] 当前状态中的消息数量: {len(state.get('messages', []))}")
        logger.debug(f"💰 [DEBUG] 现有资金盘报告: {state.get('capital_flow_report', 'None')}")

        # 根据股票代码格式选择数据源
        from tradingagents.utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)

        logger.debug(f"💰 [DEBUG] 股票类型检查: {ticker} -> {market_info['market_name']} ({market_info['currency_name']})")

        # 获取公司名称
        company_name = _get_company_name_for_capital_flow(ticker, market_info)
        logger.debug(f"💰 [DEBUG] 公司名称: {ticker} -> {company_name}")

        # 统一使用 get_stock_capital_flow 工具
        # 该工具用于获取股票资金面数据
        logger.info(f"💰 [资金盘分析师] 使用资金面数据工具")
        tools = [toolkit.get_stock_capital_flow]

        # 从MongoDB获取配置，如果不存在则使用默认配置
        config_manager = get_agent_config_manager()

        # 默认提示模板
        default_system_prompt = """你是一位专业的资金盘分析师，专注于分析股票资金面数据。

📋 **分析对象：**
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_name}
- 计价货币：{currency_name}（{currency_symbol}）
- 分析日期：{current_date}

🔧 **工具使用：**
你可以使用以下工具：{tool_names}
⚠️ 重要工作流程：
1. 如果消息历史中没有工具结果，立即调用 get_stock_capital_flow 工具
   - ticker: {ticker}
   - start_date: {current_date}
   - end_date: {current_date}
2. 如果消息历史中已经有工具结果（ToolMessage），立即基于工具数据生成最终分析报告
3. 不要重复调用工具！一次工具调用就足够了！
4. 接收到工具数据后，必须立即生成完整的资金面分析报告，不要再调用任何工具

📝 **输出格式要求（必须严格遵守）：**

## 📊 股票基本信息
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_name}

## 💰 主力资金分析
[在这里分析主力资金流入流出，提供具体数值和趋势判断]

## 🌊 北向资金分析
[在这里分析北向资金（沪股通、深股通）的流向情况]

## 🏛 机构资金分析
[在这里分析机构资金的动向，包括机构买入、卖出情况]

## 📊 资金流向总结
[在这里总结整体资金流向，判断资金面强弱]

## 💭 投资建议
[在这里给出明确的投资建议：买入/持有/卖出]

⚠️ **重要提醒：**
- 必须使用上述格式输出，不要自创标题格式
- 所有价格数据使用{currency_name}（{currency_symbol}）表示
- 确保在分析中正确使用公司名称"{company_name}"和股票代码"{ticker}"
- 不要在标题中使用"资金面分析报告"等自创标题
- 如果你有明确的资金面投资建议（买入/持有/卖出），请在投资建议部分明确标注
- 不要使用'最终交易建议'前缀，因为最终决策需要综合所有分析师的意见

请使用中文，基于真实数据进行分析。"""

        # 从配置管理器获取配置
        system_prompt = default_system_prompt

        if config_manager:
            # 尝试从MongoDB获取提示模板
            db_prompt_template = config_manager.get_prompt_template("capital_flow")
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
        logger.info(f"💰 [资金盘分析师] LLM类型: {llm.__class__.__name__}")
        logger.info(f"💰 [资金盘分析师] LLM模型: {getattr(llm, 'model_name', 'unknown')}")
        logger.info(f"💰 [资金盘分析师] 消息历史数量: {len(state['messages'])}")
        logger.info(f"💰 [资金盘分析师] 公司名称: {company_name}")
        logger.info(f"💰 [资金盘分析师] 股票代码: {ticker}")

        # 打印提示词模板信息
        logger.info("💰 [资金盘分析师] ========== 提示词模板信息 ==========")
        logger.info(f"💰 [资金盘分析师] 模板变量已设置: company_name={company_name}, ticker={ticker}, market={market_info['market_name']}")
        logger.info("💰 [资金盘分析师] ==========================================")

        # 打印实际传递给LLM的消息
        logger.info(f"💰 [资金盘分析师] ========== 传递给LLM的消息 ==========")
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
            logger.info(f"💰 [资金盘分析师] 消息[{i}] 类型={msg_type}, 内容={msg_content}")
        logger.info(f"💰 [资金盘分析师] ========== 消息列表结束 ==========")

        # 使用统一的LLM链创建工具（支持DeepSeek/302AI等模型）
        log_model_usage(llm, "资金盘分析师")
        chain = create_llm_chain(
            prompt=prompt,
            llm=llm,
            tools=tools,
            bind_tools=True,
            analyst_name="资金盘分析师"
        )

        logger.info(f"💰 [资金盘分析师] 开始调用LLM...")
        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})
        logger.info(f"💰 [资金盘分析师] LLM调用完成")

        # 打印LLM响应
        logger.info(f"💰 [资金盘分析师] ========== LLM响应开始 ==========")
        logger.info(f"💰 [资金盘分析师] 响应类型: {type(result).__name__}")
        logger.info(f"💰 [资金盘分析师] 响应内容: {str(result.content)[:1000]}...")
        if hasattr(result, 'tool_calls') and result.tool_calls:
            logger.info(f"💰 [资金盘分析师] 工具调用: {result.tool_calls}")
        logger.info(f"💰 [资金盘分析师] ========== LLM响应结束 ==========")

        # 使用统一的Google工具调用处理器
        if should_use_tool_call_handler(llm):
            logger.info(f"💰 [资金盘分析师] 检测到Google模型，使用统一工具调用处理器")

            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="资金面分析",
                specific_requirements="重点关注主力资金流向、北向资金、机构资金动向等资金指标。"
            )

            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="资金盘分析师"
            )

            return {
                "messages": [result],
                "capital_flow_report": report
            }
        else:
            # 非Google模型的处理逻辑
            logger.info(f"💰 [资金盘分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            logger.info(f"💰 [资金盘分析师] 检查LLM返回结果...")
            logger.info(f"💰 [资金盘分析师] - 是否有tool_calls: {hasattr(result, 'tool_calls')}")
            if hasattr(result, 'tool_calls'):
                logger.info(f"💰 [资金盘分析师] - tool_calls数量: {len(result.tool_calls)}")
                if result.tool_calls:
                    for i, tc in enumerate(result.tool_calls):
                        logger.info(f"💰 [资金盘分析师] - tool_call[{i}]: {tc.get('name', 'unknown')}")

            # 处理资金盘分析报告
            # 检查是否有真正的tool_calls对象
            has_real_tool_calls = hasattr(result, 'tool_calls') and len(result.tool_calls) > 0

            # 对于DeepSeek等模型，检查内容中是否包含工具调用格式的文本
            content_str = str(result.content) if hasattr(result, 'content') else ""
            has_tool_call_in_content = ('"ticker"' in content_str or '"stock_code"' in content_str) and \
                                       ('get_stock_capital_flow' in content_str or 'get_stock_sentiment' in content_str or 
                                        ('{' in content_str and '}' in content_str and ('start_date' in content_str or 'end_date' in content_str)))

            if not has_real_tool_calls and has_tool_call_in_content:
                logger.info(f"💰 [资金盘分析师] 🔍 检测到内容中包含工具调用格式（DeepSeek/302AI模型），尝试解析并执行工具...")
                logger.info(f"💰 [资金盘分析师] 内容预览: {content_str[:500]}...")

                # 🔥 修复：对于DeepSeek/302AI等模型，它们可能以文本形式输出工具调用
                # 需要解析内容中的工具调用并执行，然后基于结果生成报告
                try:
                    import re
                    from langchain_core.messages import ToolMessage, HumanMessage

                    # 尝试从内容中提取JSON格式的工具调用
                    # 查找类似 {"ticker": "...", "start_date": "...", "end_date": "..."} 的JSON
                    json_pattern = r'\{[^{}]*"ticker"[^{}]*\}'
                    json_matches = re.findall(json_pattern, content_str)

                    if json_matches:
                        logger.info(f"💰 [资金盘分析师] 从内容中提取到 {len(json_matches)} 个JSON工具调用")
                        tool_messages = []

                        for json_str in json_matches:
                            try:
                                tool_args = json.loads(json_str)
                                logger.info(f"💰 [资金盘分析师] 解析工具参数: {tool_args}")

                                # 执行工具
                                tool_result = None
                                for tool in tools:
                                    tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                                    if 'get_stock_capital_flow' in tool_name:
                                        try:
                                            # 🔧 修复：使用 invoke 方法调用 StructuredTool
                                            tool_result = tool.invoke(tool_args)
                                            logger.info(f"💰 [资金盘分析师] ✅ 工具执行成功，结果长度: {len(str(tool_result))}")
                                            break
                                        except Exception as tool_error:
                                            logger.error(f"❌ [资金盘分析师] 工具执行失败: {tool_error}")
                                            tool_result = f"工具执行失败: {str(tool_error)}"

                                if tool_result:
                                    tool_message = ToolMessage(
                                        content=str(tool_result),
                                        tool_call_id=f"parsed_{len(tool_messages)}"
                                    )
                                    tool_messages.append(tool_message)

                            except json.JSONDecodeError as e:
                                logger.warning(f"💰 [资金盘分析师] JSON解析失败: {e}")
                                continue

                        if tool_messages:
                            # 基于工具结果生成分析报告（复用已有的分析提示词）
                            analysis_prompt = f"""现在请基于上述工具获取的数据，生成详细的资金面分析报告。

**分析对象：**
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_info['market_name']}
- 计价货币：{market_info['currency_name']}（{market_info['currency_symbol']}）

请按照专业格式输出完整的资金面分析报告，包括：
1. 股票基本信息
2. 主力资金分析（流入流出、净流入）
3. 北向资金分析（沪股通、深股通流向）
4. 机构资金分析（机构买卖动向）
5. 资金流向总结（整体判断）
6. 投资建议（买入/持有/卖出，目标价位，止损位等）

报告必须基于工具返回的真实数据进行分析，包含具体的资金流向数值，长度不少于800字，使用中文撰写。"""

                            messages = state["messages"] + [result] + tool_messages + [HumanMessage(content=analysis_prompt)]
                            final_result = llm.invoke(messages)
                            report = final_result.content

                            logger.info(f"💰 [资金盘分析师] ✅ 基于工具结果生成完整分析报告，长度: {len(report)}")

                            # 返回包含工具调用和最终分析的完整消息序列
                            return {
                                "messages": [result] + tool_messages + [final_result],
                                "capital_flow_report": report
                            }
                        else:
                            logger.warning(f"💰 [资金盘分析师] ⚠️ 未能成功执行任何工具，返回原始内容")
                            report = str(result.content)
                            return {
                                "messages": [result],
                                "capital_flow_report": report
                            }
                    else:
                        logger.warning(f"💰 [资金盘分析师] ⚠️ 未能在内容中提取到JSON工具调用，返回原始内容")
                        report = str(result.content)
                        return {
                            "messages": [result],
                            "capital_flow_report": report
                        }
                except Exception as e:
                    logger.error(f"❌ [资金盘分析师] 解析工具调用时发生错误: {e}")
                    logger.error(f"❌ [资金盘分析师] 错误堆栈: {traceback.format_exc()}")
                    # 降级处理：直接使用原始内容
                    report = str(result.content)
                    logger.info(f"💰 [资金盘分析师] ⚠️ 降级处理，返回原始内容，长度: {len(report)}")
                    return {
                        "messages": [result],
                        "capital_flow_report": report
                    }
            elif has_real_tool_calls:
                # 有工具调用，执行工具并生成完整分析报告
                logger.info(f"💰 [资金盘分析师] 🔧 检测到工具调用: {[call.get('name', 'unknown') for call in result.tool_calls]}")

                try:
                    # 执行工具调用
                    from langchain_core.messages import ToolMessage, HumanMessage

                    tool_messages = []
                    for tool_call in result.tool_calls:
                        tool_name = tool_call.get('name')
                        tool_args = tool_call.get('args', {})
                        tool_id = tool_call.get('id')

                        # 🔧 修复：处理不同格式的 tool_calls
                        # 有些模型可能使用 'arguments' 字段（JSON 字符串）
                        if not tool_args and 'arguments' in tool_call:
                            import json
                            try:
                                tool_args = json.loads(tool_call['arguments'])
                            except (json.JSONDecodeError, TypeError):
                                logger.warning(f"⚠️ [工具调用] 无法解析 arguments 字段: {tool_call.get('arguments')}")
                                tool_args = {}

                        logger.debug(f"💰 [DEBUG] 执行工具: {tool_name}, 参数: {tool_args}")

                        # 找到对应的工具并执行
                        tool_result = None
                        for tool in tools:
                            # 安全地获取工具名称进行比较
                            current_tool_name = None
                            if hasattr(tool, 'name'):
                                current_tool_name = tool.name
                            elif hasattr(tool, '__name__'):
                                current_tool_name = tool.__name__

                            if current_tool_name == tool_name:
                                try:
                                    # 🔧 修复：使用 invoke 方法调用 StructuredTool
                                    tool_result = tool.invoke(tool_args)
                                    logger.debug(f"💰 [DEBUG] 工具执行成功，结果长度: {len(str(tool_result))}")
                                    break
                                except Exception as tool_error:
                                    logger.error(f"❌ [DEBUG] 工具执行失败: {tool_error}")
                                    tool_result = f"工具执行失败: {str(tool_error)}"

                        if tool_result:
                            tool_message = ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_id
                            )
                            tool_messages.append(tool_message)

                    # 基于工具结果生成分析报告
                    analysis_prompt = f"""现在请基于上述工具获取的数据，生成详细的资金面分析报告。

**分析对象：**
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_info['market_name']}
- 计价货币：{market_info['currency_name']}（{market_info['currency_symbol']}）

请按照专业格式输出完整的资金面分析报告，包括：
1. 股票基本信息
2. 主力资金分析（流入流出、净流入）
3. 北向资金分析（沪股通、深股通流向）
4. 机构资金分析（机构买卖动向）
5. 资金流向总结（整体判断）
6. 投资建议（买入/持有/卖出，目标价位，止损位等）

报告必须基于工具返回的真实数据进行分析，包含具体的资金流向数值，长度不少于800字，使用中文撰写。"""

                    messages = state["messages"] + [result] + tool_messages + [HumanMessage(content=analysis_prompt)]
                    final_result = llm.invoke(messages)
                    report = final_result.content

                    logger.info(f"💰 [资金盘分析师] 生成完整分析报告，长度: {len(report)}")

                    return {
                        "messages": [result] + tool_messages + [final_result],
                        "capital_flow_report": report
                    }
                except Exception as e:
                    logger.error(f"❌ [资金盘分析师] 工具执行或分析生成失败: {e}")
                    logger.error(f"❌ [资金盘分析师] 错误堆栈: {traceback.format_exc()}")
                    report = f"资金盘分析师调用了工具但分析生成失败: {[call.get('name', 'unknown') for call in result.tool_calls]}"
                    return {
                        "messages": [result],
                        "capital_flow_report": report
                    }
            else:
                # 没有工具调用，直接使用LLM返回的内容
                logger.info(f"💰 [资金盘分析师] ✅ 直接回复（无工具调用），长度: {len(result.content)}")
                report = str(result.content)
                return {
                    "messages": [result],
                    "capital_flow_report": report
                }

    return capital_flow_analyst_node
