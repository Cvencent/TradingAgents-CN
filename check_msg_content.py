#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查消息内容"""

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
    
    print("\nChecking each message:")
    for i, msg in enumerate(messages):
        if isinstance(msg, dict):
            msg_type = msg.get('type', 'unknown')
            content = msg.get('content', '')
            
            print(f"\n[{i}] Type: {msg_type}")
            if content:
                content_preview = content[:200] if len(content) > 200 else content
                print(f"    Content preview: {content_preview}")
                
                # 检查是否包含关键词
                content_lower = content.lower()
                found_keywords = []
                for analyst_key, keywords in analyst_keywords.items():
                    for keyword in keywords:
                        if keyword.lower() in content_lower:
                            found_keywords.append(f"{analyst_key}({keyword})")
                            break
                
                if found_keywords:
                    print(f"    Found keywords: {found_keywords}")
                else:
                    print(f"    No keywords found")
        else:
            print(f"\n[{i}] Not a dict: {type(msg).__name__}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
