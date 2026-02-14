#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试prompts提取过程"""

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
        'market_report': ['market analyst', '市场分析师', '技术面分析', '技术分析师', '股票趋势分析', '市场趋势'],
        'fundamentals_report': ['fundamentals analyst', '基本面分析师', '基本面分析', '公司基本信息'],
        'sentiment_report': ['sentiment analyst', '情绪分析师', '市场情绪分析', 'sentiment'],
        'news_report': ['news analyst', '新闻分析师', '新闻事件分析', '新闻舆情'],
        'bull_researcher': ['bull researcher', '多头研究员', 'bullish', '看涨', '牛市'],
        'bear_researcher': ['bear researcher', '空头研究员', 'bearish', '看跌', '熊市'],
        'risky_analyst': ['risky analyst', '激进分析师', '激进风险评估', '激进'],
        'safe_analyst': ['safe analyst', '保守分析师', '保守风险评估', '保守'],
        'neutral_analyst': ['neutral analyst', '中性分析师', '中性风险评估', '中性'],
        'trader_investment_plan': ['trader', '交易员', '交易计划', '投资策略'],
        'final_trade_decision': ['final decision', '最终决策', '最终交易决策', '投资建议'],
    }
    
    # 为每个分析师收集消息
    analyst_messages = {key: [] for key in analyst_mapping.keys()}
    
    for msg in messages:
        if isinstance(msg, dict):
            msg_type = msg.get('type', '')
            msg_content = msg.get('content', '')
            
            if msg_type in ['system', 'remove'] or not msg_content:
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
    
    # 打印每个分析师的消息统计
    print("\n" + "="*80)
    print("Analyst Messages Statistics:")
    print("="*80)
    
    for analyst_key, msg_list in analyst_messages.items():
        if not msg_list:
            continue
        
        # 计算总长度
        total_length = sum(len(msg['content']) for msg in msg_list)
        
        # 构建prompt内容
        prompt_content = f"=== {analyst_mapping.get(analyst_key, analyst_key)} ===\n\n"
        for msg in msg_list:
            prompt_content += f"\n[{msg['type'].upper()}]\n{msg['content'][:3000]}\n"
        
        print(f"\n{analyst_key}:")
        print(f"  Messages count: {len(msg_list)}")
        print(f"  Total content length: {total_length}")
        print(f"  Prompt content length: {len(prompt_content)}")
        print(f"  Will be included: {'YES' if len(prompt_content) > 100 else 'NO (too short)'}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
