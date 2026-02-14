from langchain_core.messages import AIMessage
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")

        # 🔧 修复：使用 .get() 安全访问，可能不存在
        trader_decision = state.get("trader_investment_plan", "[暂无交易员决策]")

        # 📊 记录输入数据长度
        logger.info(f"📊 [Safe Analyst] 输入数据长度统计:")
        logger.info(f"  - market_report: {len(market_research_report):,} 字符")
        logger.info(f"  - sentiment_report: {len(sentiment_report):,} 字符")
        logger.info(f"  - news_report: {len(news_report):,} 字符")
        logger.info(f"  - fundamentals_report: {len(fundamentals_report):,} 字符")
        logger.info(f"  - trader_decision: {len(trader_decision):,} 字符")
        logger.info(f"  - history: {len(history):,} 字符")
        total_length = (len(market_research_report) + len(sentiment_report) +
                       len(news_report) + len(fundamentals_report) +
                       len(trader_decision) + len(history) +
                       len(current_risky_response) + len(current_neutral_response))
        logger.info(f"  - 总Prompt长度: {total_length:,} 字符 (~{total_length//4:,} tokens)")

        prompt = f"""作为安全/保守风险分析师，您的主要目标是保护资产、最小化波动性，并确保稳定、可靠的增长。您优先考虑稳定性、安全性和风险缓解，仔细评估潜在损失、经济衰退和市场波动。在评估交易员的决策或计划时，请批判性地审查高风险要素，指出决策可能使公司面临不当风险的地方，以及更谨慎的替代方案如何能够确保长期收益。以下是交易员的决策：

{trader_decision}

您的任务是积极反驳激进和中性分析师的论点，突出他们的观点可能忽视的潜在威胁或未能优先考虑可持续性的地方。直接回应他们的观点，利用以下数据来源为交易员决策的低风险方法调整建立令人信服的案例：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
以下是当前对话历史：{history} 以下是激进分析师的最后回应：{current_risky_response} 以下是中性分析师的最后回应：{current_neutral_response}。如果其他观点没有回应，请不要虚构，只需提出您的观点。

通过质疑他们的乐观态度并强调他们可能忽视的潜在下行风险来参与讨论。解决他们的每个反驳点，展示为什么保守立场最终是公司资产最安全的道路。专注于辩论和批评他们的论点，证明低风险策略相对于他们方法的优势。请用中文以对话方式输出，就像您在说话一样，不使用任何特殊格式。"""

        logger.info(f"⏱️ [Safe Analyst] 开始调用LLM...")
        llm_start_time = time.time()

        response = llm.invoke(prompt)

        llm_elapsed = time.time() - llm_start_time
        logger.info(f"⏱️ [Safe Analyst] LLM调用完成，耗时: {llm_elapsed:.2f}秒")

        argument = f"Safe Analyst: {response.content}"

        new_count = risk_debate_state["count"] + 1
        logger.info(f"🛡️ [保守风险分析师] 发言完成，计数: {risk_debate_state['count']} -> {new_count}")

        # 兼容旧格式（字符串）和新格式（列表）
        current_safe_history = risk_debate_state.get("safe_history", "")
        if isinstance(current_safe_history, list):
            # 新格式：列表，追加当前轮次
            new_safe_history = current_safe_history + [argument]
        else:
            # 旧格式：字符串，转换为列表并追加
            if current_safe_history:
                new_safe_history = [current_safe_history, argument]
            else:
                new_safe_history = [argument]

        # 🔧 保存当前prompt到safe_prompts列表（用于前端展示）
        current_safe_prompts = risk_debate_state.get("safe_prompts", [])
        if not isinstance(current_safe_prompts, list):
            current_safe_prompts = []
        new_safe_prompts = current_safe_prompts + [prompt]
        logger.info(f"🔍 [Safe Analyst] 保存prompt到safe_prompts，当前轮数: {len(new_safe_prompts)}, prompt长度: {len(prompt)} chars")

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": new_safe_history,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": new_count,
            "safe_prompts": new_safe_prompts,  # 🔧 保存prompts
        }

        logger.info(f"🔍 [Safe Analyst] 返回risk_debate_state，包含字段: {list(new_risk_debate_state.keys())}")
        
        # 🔥 关键修复：同时返回 safe_request_prompt 字段（用于前端展示原始prompt）
        # 将所有轮次的prompt合并，用分隔符隔开
        full_safe_prompt = "\n\n" + "="*60 + "\n【保守分析师 - 多轮辩论Prompts】\n" + "="*60 + "\n\n"
        for i, p in enumerate(new_safe_prompts, 1):
            full_safe_prompt += f"\n--- 第 {i} 轮 ---\n{p}\n"
        
        logger.info(f"🔍 [Safe Analyst] 返回 safe_request_prompt，总长度: {len(full_safe_prompt)} chars")
        return {
            "risk_debate_state": new_risk_debate_state,
            "safe_request_prompt": full_safe_prompt  # 🔥 保存完整的请求prompt
        }

    return safe_node
