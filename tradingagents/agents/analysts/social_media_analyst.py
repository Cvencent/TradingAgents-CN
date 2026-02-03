from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
logger = get_logger("analysts.social_media")

# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler

# 导入LLM链创建工具
from tradingagents.agents.utils.llm_chain_utils import (
    create_llm_chain,
    should_use_tool_call_handler,
    log_model_usage
)


def _get_company_name_for_social_media(ticker: str, market_info: dict) -> str:
    """
    为社交媒体分析师获取公司名称

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

            logger.debug(f"📊 [社交媒体分析师] 获取股票信息返回: {stock_info[:200] if stock_info else 'None'}...")

            # 解析股票名称
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [社交媒体分析师] 成功获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                # 降级方案：尝试直接从数据源管理器获取
                logger.warning(f"⚠️ [社交媒体分析师] 无法从统一接口解析股票名称: {ticker}，尝试降级方案")
                try:
                    from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                    info_dict = get_info_dict(ticker)
                    if info_dict and info_dict.get('name'):
                        company_name = info_dict['name']
                        logger.info(f"✅ [社交媒体分析师] 降级方案成功获取股票名称: {ticker} -> {company_name}")
                        return company_name
                except Exception as e:
                    logger.error(f"❌ [社交媒体分析师] 降级方案也失败: {e}")

                logger.error(f"❌ [社交媒体分析师] 所有方案都无法获取股票名称: {ticker}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"📊 [社交媒体分析师] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"📊 [社交媒体分析师] 改进港股工具获取名称失败: {e}")
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
            logger.debug(f"📊 [社交媒体分析师] 美股名称映射: {ticker} -> {company_name}")
            return company_name

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"❌ [社交媒体分析师] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_social_media_analyst(llm, toolkit):
    @log_analyst_module("social_media")
    def social_media_analyst_node(state):
        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("sentiment_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # 获取股票市场信息
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)

        # 获取公司名称
        company_name = _get_company_name_for_social_media(ticker, market_info)
        logger.info(f"[社交媒体分析师] 公司名称: {company_name}")

        # 统一使用 get_stock_sentiment_unified 工具
        # 该工具内部会自动识别股票类型并调用相应的情绪数据源
        logger.info(f"[社交媒体分析师] 使用统一情绪分析工具，自动识别股票类型")
        tools = [toolkit.get_stock_sentiment_unified]

        system_message = (
            """您是一位专业的中国市场社交媒体和投资情绪分析师，负责分析中国投资者对特定股票的讨论和情绪变化。

您的主要职责包括：
1. 分析中国主要财经平台的投资者情绪（如雪球、东方财富股吧等）
2. 监控财经媒体和新闻对股票的报道倾向
3. 识别影响股价的热点事件和市场传言
4. 评估散户与机构投资者的观点差异
5. 分析政策变化对投资者情绪的影响
6. 评估情绪变化对股价的潜在影响

重点关注平台：
- 财经新闻：财联社、新浪财经、东方财富、腾讯财经
- 投资社区：雪球、东方财富股吧、同花顺
- 社交媒体：微博财经大V、知乎投资话题
- 专业分析：各大券商研报、财经自媒体

分析要点：
- 投资者情绪的变化趋势和原因
- 关键意见领袖(KOL)的观点和影响力
- 热点事件对股价预期的影响
- 政策解读和市场预期变化
- 散户情绪与机构观点的差异

📊 情绪影响分析要求：
- 量化投资者情绪强度（乐观/悲观程度）和情绪变化趋势
- 评估情绪变化对短期市场反应的影响（1-5天）
- 分析散户情绪与市场走势的相关性
- 识别情绪极端点和可能的情绪反转信号
- 提供基于情绪分析的市场预期和投资建议
- 评估市场情绪对投资者信心和决策的影响程度
- 不允许回复'无法评估情绪影响'或'需要更多数据'

💰 必须包含：
- 情绪指数评分（1-10分）
- 预期价格波动幅度
- 基于情绪的交易时机建议

请撰写详细的中文分析报告，并在报告末尾附上Markdown表格总结关键发现。
注意：由于中国社交媒体API限制，如果数据获取受限，请明确说明并提供替代分析建议。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位有用的AI助手，与其他助手协作。"
                    " 使用提供的工具来推进回答问题。"
                    " 如果您无法完全回答，没关系；具有不同工具的其他助手"
                    " 将从您停下的地方继续帮助。执行您能做的以取得进展。"
                    " 如果您或任何其他助手有最终交易提案：**买入/持有/卖出**或可交付成果，"
                    " 请在您的回应前加上最终交易提案：**买入/持有/卖出**，以便团队知道停止。"
                    " 您可以访问以下工具：{tool_names}。\n{system_message}"
                    "供您参考，当前日期是{current_date}。我们要分析的当前公司是{ticker}。请用中文撰写所有分析内容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]  
        )

        prompt = prompt.partial(system_message=system_message)
        # 安全地获取工具名称，处理函数和工具对象
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))

        prompt = prompt.partial(tool_names=", ".join(tool_names))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        # 使用统一的LLM链创建工具（支持DeepSeek/302AI等模型）
        log_model_usage(llm, "社交媒体分析师")
        chain = create_llm_chain(
            prompt=prompt,
            llm=llm,
            tools=tools,
            bind_tools=True,
            analyst_name="社交媒体分析师"
        )

        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})

        # 使用统一的Google工具调用处理器
        if should_use_tool_call_handler(llm):
            logger.info(f"📊 [社交媒体分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="社交媒体情绪分析",
                specific_requirements="重点关注投资者情绪、社交媒体讨论热度、舆论影响等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="社交媒体分析师"
            )
        else:
            # 非Google模型的处理逻辑
            logger.info(f"📊 [社交媒体分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            
            report = ""
            # 检查是否有真正的tool_calls对象
            has_real_tool_calls = hasattr(result, 'tool_calls') and len(result.tool_calls) > 0
            
            # 对于DeepSeek等模型，检查内容中是否包含工具调用格式的文本
            content_str = str(result.content) if hasattr(result, 'content') else ""
            has_tool_call_in_content = ('"ticker"' in content_str or 'stock_sentiment' in content_str or 
                                        'get_stock_sentiment_unified' in content_str) and \
                                       ('{' in content_str and '}' in content_str)
            
            if not has_real_tool_calls and has_tool_call_in_content:
                logger.info(f"📊 [社交媒体分析师] 🔍 检测到内容中包含工具调用格式（DeepSeek/302AI模型），尝试解析并执行工具...")
                logger.info(f"📊 [社交媒体分析师] 内容预览: {content_str[:500]}...")
                
                # 🔥 修复：对于DeepSeek/302AI等模型，它们可能以文本形式输出工具调用
                # 需要解析内容中的工具调用并执行，然后基于结果生成报告
                try:
                    import re
                    from langchain_core.messages import ToolMessage, HumanMessage
                    
                    # 尝试从内容中提取JSON格式的工具调用
                    # 查找类似 {"stock_code": "...", "days": ...} 的JSON
                    json_pattern = r'\{[^{}]*"stock_code"[^{}]*\}'
                    json_matches = re.findall(json_pattern, content_str)
                    
                    if not json_matches:
                        # 尝试更宽泛的JSON匹配
                        json_pattern = r'\{[^{}]*"ticker"[^{}]*\}'
                        json_matches = re.findall(json_pattern, content_str)
                    
                    if json_matches:
                        logger.info(f"📊 [社交媒体分析师] 从内容中提取到 {len(json_matches)} 个JSON工具调用")
                        tool_messages = []
                        
                        for json_str in json_matches:
                            try:
                                tool_args = json.loads(json_str)
                                logger.info(f"📊 [社交媒体分析师] 解析工具参数: {tool_args}")
                                
                                # 执行工具
                                tool_result = None
                                for tool in tools:
                                    tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                                    if 'get_stock_sentiment_unified' in tool_name:
                                        try:
                                            # 🔧 修复：直接调用函数，因为工具是普通函数而非LangChain Tool对象
                                            tool_result = tool(**tool_args)
                                            logger.info(f"📊 [社交媒体分析师] ✅ 工具执行成功，结果长度: {len(str(tool_result))}")
                                            break
                                        except Exception as tool_error:
                                            logger.error(f"❌ [社交媒体分析师] 工具执行失败: {tool_error}")
                                            tool_result = f"工具执行失败: {str(tool_error)}"
                                
                                if tool_result:
                                    tool_message = ToolMessage(
                                        content=str(tool_result),
                                        tool_call_id=f"parsed_{len(tool_messages)}"
                                    )
                                    tool_messages.append(tool_message)
                                    
                            except json.JSONDecodeError as e:
                                logger.warning(f"📊 [社交媒体分析师] JSON解析失败: {e}")
                                continue
                        
                        if tool_messages:
                            # 基于工具结果生成分析报告
                            analysis_prompt = f"""基于上述工具获取的社交媒体情绪数据，生成详细的情绪分析报告。

**分析对象：**
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_info['market_name']}

**输出格式要求：**

# **{company_name}（{ticker}）市场情绪分析报告**

## 一、市场情绪概况

[总结整体市场情绪，包括投资者信心、讨论热度等]

## 二、社交媒体情绪分析

### 1. 投资者情绪指标
- 情绪指数评分（1-10分）
- 乐观/悲观程度
- 情绪变化趋势

### 2. 讨论热度分析
- 社交媒体讨论量
- 关键话题和热点
- 意见领袖观点

## 三、情绪影响评估

### 1. 对股价的潜在影响
- 短期影响（1-5天）
- 中期影响（1-4周）

### 2. 投资建议
- 基于情绪的交易时机建议
- 风险提示

请用中文撰写详细的分析报告。"""
                            
                            messages = state["messages"] + [result] + tool_messages + [HumanMessage(content=analysis_prompt)]
                            final_result = llm.invoke(messages)
                            report = final_result.content
                            
                            logger.info(f"📊 [社交媒体分析师] ✅ 基于工具结果生成完整分析报告，长度: {len(report)}")
                            
                            # 返回包含工具调用和最终分析的完整消息序列
                            return {
                                "messages": [result] + tool_messages + [final_result],
                                "sentiment_report": report,
                                "sentiment_tool_call_count": tool_call_count + 1
                            }
                        else:
                            logger.warning(f"📊 [社交媒体分析师] ⚠️ 未能成功执行任何工具，返回原始内容")
                            report = content_str
                    else:
                        logger.warning(f"📊 [社交媒体分析师] ⚠️ 未能在内容中提取到JSON工具调用，返回原始内容")
                        report = content_str
                        
                except Exception as e:
                    logger.error(f"❌ [社交媒体分析师] 解析工具调用时发生错误: {e}")
                    import traceback
                    logger.error(f"异常堆栈: {traceback.format_exc()}")
                    # 降级处理：返回原始内容
                    report = content_str
                    logger.info(f"📊 [社交媒体分析师] ⚠️ 降级处理，返回原始内容，长度: {len(report)}")
            elif not has_real_tool_calls:
                # 没有工具调用，直接使用LLM的回复
                report = result.content
                logger.info(f"📊 [社交媒体分析师] ✅ 直接回复（无工具调用），长度: {len(report)}")
            else:
                # 有工具调用，执行工具并生成完整分析报告
                logger.info(f"📊 [社交媒体分析师] 🔧 检测到工具调用: {[call.get('name', 'unknown') for call in result.tool_calls]}")
                
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
                        
                        logger.debug(f"📊 [DEBUG] 执行工具: {tool_name}, 参数: {tool_args}")
                        
                        # 找到对应的工具并执行
                        tool_result = None
                        for tool in tools:
                            current_tool_name = None
                            if hasattr(tool, 'name'):
                                current_tool_name = tool.name
                            elif hasattr(tool, '__name__'):
                                current_tool_name = tool.__name__
                            
                            if current_tool_name == tool_name:
                                try:
                                    # 🔧 修复：直接调用函数，因为工具是普通函数而非LangChain Tool对象
                                    tool_result = tool(**tool_args)
                                    logger.debug(f"📊 [DEBUG] 工具执行成功，结果长度: {len(str(tool_result))}")
                                    break
                                except Exception as tool_error:
                                    logger.error(f"❌ [DEBUG] 工具执行失败: {tool_error}")
                                    tool_result = f"工具执行失败: {str(tool_error)}"
                        
                        if tool_result is None:
                            tool_result = f"未找到工具: {tool_name}"
                        
                        # 创建工具消息
                        tool_message = ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_id
                        )
                        tool_messages.append(tool_message)
                    
                    # 基于工具结果生成完整分析报告
                    analysis_prompt = f"""基于上述工具获取的社交媒体情绪数据，生成详细的情绪分析报告。

**分析对象：**
- 公司名称：{company_name}
- 股票代码：{ticker}

**输出格式要求：**

# **{company_name}（{ticker}）市场情绪分析报告**

## 一、市场情绪概况

[总结整体市场情绪，包括投资者信心、讨论热度等]

## 二、社交媒体情绪分析

### 1. 投资者情绪指标
- 情绪指数评分（1-10分）
- 乐观/悲观程度
- 情绪变化趋势

### 2. 讨论热度分析
- 社交媒体讨论量
- 关键话题和热点
- 意见领袖观点

## 三、情绪影响评估

### 1. 对股价的潜在影响
- 短期影响（1-5天）
- 中期影响（1-4周）

### 2. 投资建议
- 基于情绪的交易时机建议
- 风险提示

请用中文撰写详细的分析报告。"""
                    
                    # 构建消息列表进行最终分析
                    final_messages = state["messages"] + [result] + tool_messages + [HumanMessage(content=analysis_prompt)]
                    
                    logger.info(f"📊 [社交媒体分析师] 🔄 基于工具结果生成最终报告...")
                    final_result = llm.invoke(final_messages)
                    report = final_result.content
                    logger.info(f"📊 [社交媒体分析师] ✅ 报告生成完成，长度: {len(report)}")
                    
                except Exception as e:
                    logger.error(f"❌ [社交媒体分析师] 工具调用处理失败: {e}")
                    import traceback
                    logger.error(f"📋 异常堆栈: {traceback.format_exc()}")
                    # 降级：返回原始内容
                    report = result.content

        # 🔧 更新工具调用计数器
        return {
            "messages": [result],
            "sentiment_report": report,
            "sentiment_tool_call_count": tool_call_count + 1
        }

    return social_media_analyst_node
