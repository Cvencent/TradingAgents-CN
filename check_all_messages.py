#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有消息，看看为什么只有 Fundamentals Analyst 被提取"""

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
    
    # 完整的关键词映射
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
    
    print("\n" + "="*80)
    print("Analyzing all messages for analyst keywords...")
    print("="*80)
    
    for i, msg in enumerate(messages):
        if isinstance(msg, dict):
            msg_type = msg.get('type', 'unknown')
            content = msg.get('content', '')
            
            print(f"\n[{i}] Type: {msg_type}")
            
            if content:
                content_preview = content[:150] if len(content) > 150 else content
                print(f"    Content: {content_preview}")
                
                # 检查是否包含关键词
                content_lower = content.lower()
                found_keywords = []
                for analyst_key, keywords in analyst_keywords.items():
                    for keyword in keywords:
                        if keyword.lower() in content_lower:
                            found_keywords.append(f"{analyst_key}({keyword})")
                            break
                
                if found_keywords:
                    print(f"    ✓ Found: {found_keywords}")
                else:
                    print(f"    ✗ No keywords found")
            else:
                print(f"    (empty content)")
    
    # 同时检查 reports 字段
    print("\n" + "="*80)
    print("Reports in database:")
    print("="*80)
    reports = report.get("reports", {})
    for key in reports.keys():
        print(f"  - {key}")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
