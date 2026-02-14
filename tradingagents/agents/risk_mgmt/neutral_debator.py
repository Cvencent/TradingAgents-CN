import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state.get("fundamentals_report", "")

        # 🔧 修复：使用 .get() 安全访问，可能不存在
        trader_decision = state.get("trader_investment_plan", "[暂无交易员决策]")

        # 📊 记录所有输入数据的长度，用于性能分析
        logger.info(f"📊 [Neutral Analyst] 输入数据长度统计:")
        logger.info(f"  - market_report: {len(market_research_report):,} 字符 (~{len(market_research_report)//4:,} tokens)")
        logger.info(f"  - sentiment_report: {len(sentiment_report):,} 字符 (~{len(sentiment_report)//4:,} tokens)")
        logger.info(f"  - news_report: {len(news_report):,} 字符 (~{len(news_report)//4:,} tokens)")
        logger.info(f"  - fundamentals_report: {len(fundamentals_report):,} 字符 (~{len(fundamentals_report)//4:,} tokens)")
        logger.info(f"  - trader_decision: {len(trader_decision):,} 字符 (~{len(trader_decision)//4:,} tokens)")
        logger.info(f"  - history: {len(history):,} 字符 (~{len(history)//4:,} tokens)")
        logger.info(f"  - current_risky_response: {len(current_risky_response):,} 字符 (~{len(current_risky_response)//4:,} tokens)")
        logger.info(f"  - current_safe_response: {len(current_safe_response):,} 字符 (~{len(current_safe_response)//4:,} tokens)")

        # 计算总prompt长度
        total_prompt_length = (len(market_research_report) + len(sentiment_report) +
                              len(news_report) + len(fundamentals_report) +
                              len(trader_decision) + len(history) +
                              len(current_risky_response) + len(current_safe_response))
        logger.info(f"  - 🚨 总Prompt长度: {total_prompt_length:,} 字符 (~{total_prompt_length//4:,} tokens)")

        prompt = f"""作为中性风险分析师，您的角色是提供平衡的视角，权衡交易员决策或计划的潜在收益和风险。您优先考虑全面的方法，评估上行和下行风险，同时考虑更广泛的市场趋势、潜在的经济变化和多元化策略。以下是交易员的决策：

{trader_decision}

您的任务是挑战激进和安全分析师，指出每种观点可能过于乐观或过于谨慎的地方。使用以下数据来源的见解来支持调整交易员决策的温和、可持续策略：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
以下是当前对话历史：{history} 以下是激进分析师的最后回应：{current_risky_response} 以下是安全分析师的最后回应：{current_safe_response}。如果其他观点没有回应，请不要虚构，只需提出您的观点。

通过批判性地分析双方来积极参与，解决激进和保守论点中的弱点，倡导更平衡的方法。挑战他们的每个观点，说明为什么适度风险策略可能提供两全其美的效果，既提供增长潜力又防范极端波动。专注于辩论而不是简单地呈现数据，旨在表明平衡的观点可以带来最可靠的结果。请用中文以对话方式输出，就像您在说话一样，不使用任何特殊格式。"""

        logger.info(f"⏱️ [Neutral Analyst] 开始调用LLM...")
        llm_start_time = time.time()

        response = llm.invoke(prompt)

        llm_elapsed = time.time() - llm_start_time
        logger.info(f"⏱️ [Neutral Analyst] LLM调用完成，耗时: {llm_elapsed:.2f}秒")
        logger.info(f"📝 [Neutral Analyst] 响应长度: {len(response.content):,} 字符")

        argument = f"Neutral Analyst: {response.content}"

        new_count = risk_debate_state["count"] + 1
        logger.info(f"📝 [Neutral Analyst] 响应长度: {len(response.content):,} 字符")
        logger.info(f"⚖️ [中性风险分析师] 发言完成，计数: {risk_debate_state['count']} -> {new_count}")

        # 兼容旧格式（字符串）和新格式（列表）
        current_neutral_history = risk_debate_state.get("neutral_history", "")
        if isinstance(current_neutral_history, list):
            # 新格式：列表，追加当前轮次
            new_neutral_history = current_neutral_history + [argument]
        else:
            # 旧格式：字符串，转换为列表并追加
            if current_neutral_history:
                new_neutral_history = [current_neutral_history, argument]
            else:
                new_neutral_history = [argument]

        # 🔧 保存当前prompt到neutral_prompts列表（用于前端展示）
        current_neutral_prompts = risk_debate_state.get("neutral_prompts", [])
        if not isinstance(current_neutral_prompts, list):
            current_neutral_prompts = []
        new_neutral_prompts = current_neutral_prompts + [prompt]
        logger.info(f"🔍 [Neutral Analyst] 保存prompt到neutral_prompts，当前轮数: {len(new_neutral_prompts)}, prompt长度: {len(prompt)} chars")

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": new_neutral_history,
            "latest_speaker": "Neutral",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "count": new_count,
            "neutral_prompts": new_neutral_prompts,  # 🔧 保存prompts
        }

        logger.info(f"🔍 [Neutral Analyst] 返回risk_debate_state，包含字段: {list(new_risk_debate_state.keys())}")
        
        # 🔥 关键修复：同时返回 neutral_request_prompt 字段（用于前端展示原始prompt）
        # 将所有轮次的prompt合并，用分隔符隔开
        full_neutral_prompt = "\n\n" + "="*60 + "\n【中性分析师 - 多轮辩论Prompts】\n" + "="*60 + "\n\n"
        for i, p in enumerate(new_neutral_prompts, 1):
            full_neutral_prompt += f"\n--- 第 {i} 轮 ---\n{p}\n"
        
        logger.info(f"🔍 [Neutral Analyst] 返回 neutral_request_prompt，总长度: {len(full_neutral_prompt)} chars")
        return {
            "risk_debate_state": new_risk_debate_state,
            "neutral_request_prompt": full_neutral_prompt  # 🔥 保存完整的请求prompt
        }

    return neutral_node
