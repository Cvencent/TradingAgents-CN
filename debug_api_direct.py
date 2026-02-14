#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""直接调试API的prompts提取逻辑"""

import sys
sys.path.insert(0, 'd:\\trade\\TradingAgents-CN')

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    task_id = "a5cc5b31-0148-48dd-a37d-5719c8a2cddc"
    
    report = db.analysis_reports.find_one({"task_id": task_id})
    if not report:
        print("Report not found")
        return 1
    
    messages = report.get("messages", [])
    print(f"Total messages: {len(messages)}")
    
    # 分析师映射
    analyst_mapping = {
        'market_report': 'Market Analyst',
        'fundamentals_report': 'Fundamentals Analyst',
        'sentiment_report': 'Sentiment Analyst',
        'news_report': 'News Analyst',
        'bull_researcher': 'Bull Researcher',
        'bear_researcher': 'Bear Researcher',
        'risky_analyst': 'Risky Analyst',
        'safe_analyst': 'Safe Analyst',
        'neutral_analyst': 'Neutral Analyst',
        'investment_plan': 'Research Team',
        'trader_investment_plan': 'Trader',
        'final_trade_decision': 'Final Decision',
    }
    
    # 关键词映射
    analyst_keywords = {
        'market_report': ['market analyst', '市场分析师', '技术面分析', '技术分析师'],
        'fundamentals_report': ['fundamentals analyst', '基本面分析师', '基本面分析'],
        'sentiment_report': ['sentiment analyst', '情绪分析师', '市场情绪分析'],
        'news_report': ['news analyst', '新闻分析师', '新闻事件分析'],
        'bull_researcher': ['bull researcher', '多头研究员', 'bullish'],
        'bear_researcher': ['bear researcher', '空头研究员', 'bearish'],
        'risky_analyst': ['risky analyst', '激进分析师', '激进风险评估'],
        'safe_analyst': ['safe analyst', '保守分析师', '保守风险评估'],
        'neutral_analyst': ['neutral analyst', '中性分析师', '中性风险评估'],
        'trader_investment_plan': ['trader', '交易员', '交易计划'],
        'final_trade_decision': ['final decision', '最终决策', '最终交易决策'],
    }
    
    prompts = []
    analyst_messages = {key: [] for key in analyst_mapping.keys()}
    
    for msg in messages:
        try:
            msg_type = msg.get('type', '') if isinstance(msg, dict) else type(msg).__name__
            msg_content = msg.get('content', '') if isinstance(msg, dict) else (msg.content if hasattr(msg, 'content') else str(msg))
            
            if msg_type in ['system', 'System', 'system', 'remove', 'Remove']:
                continue
            
            if not msg_content:
                continue
            
            # 检查这条消息属于哪些分析师
            content_lower = str(msg_content).lower()
            matched_analysts = []
            for analyst_key, keywords in analyst_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in content_lower:
                        matched_analysts.append(analyst_key)
                        break
            
            # 如果匹配到了分析师，将消息添加到对应的列表
            if matched_analysts:
                for analyst_key in matched_analysts:
                    analyst_messages[analyst_key].append({
                        'type': msg_type,
                        'content': str(msg_content)
                    })
        
        except Exception as e:
            print(f"⚠️ 处理消息时出错: {e}")
            continue
    
    # 为每个有消息的分析师创建prompt
    for analyst_key, msg_list in analyst_messages.items():
        if not msg_list:
            continue
        
        # 合并所有消息
        prompt_content = f"=== {analyst_mapping.get(analyst_key, analyst_key)} ===\n\n"
        for msg in msg_list:
            prompt_content += f"\n[{msg['type'].upper()}]\n{msg['content'][:3000]}\n"
        
        if len(prompt_content) > 100:  # 确保内容足够长
            prompts.append({
                "analyst": analyst_key,
                "analyst_name": analyst_mapping.get(analyst_key, analyst_key).replace("_", " ").title(),
                "type": "extracted",
                "content": prompt_content[:5000],
                "timestamp": ""
            })
            print(f"✅ 提取到 {analyst_key} 的prompt，共 {len(msg_list)} 条消息，长度 {len(prompt_content)}")
    
    print(f"\n总共提取到 {len(prompts)} 个prompts")
    
    # 打印每个prompt的分析师
    for i, p in enumerate(prompts):
        print(f"  [{i}] {p['analyst']} - {len(p['content'])} chars")
    
    client.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
