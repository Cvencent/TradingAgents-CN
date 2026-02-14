#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查分析师执行情况"""

from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 查找最新的报告
    report = db.analysis_reports.find_one(
        {}, 
        sort=[("created_at", -1)]
    )
    
    if not report:
        print("No report found")
        return 1
    
    print(f"Report ID: {report.get('analysis_id')}")
    print(f"Task ID: {report.get('task_id')}")
    print(f"Stock: {report.get('stock_symbol')}")
    
    # 检查reports字段
    reports = report.get("reports", {})
    print(f"\n📊 Reports field ({len(reports)} items):")
    for key, value in reports.items():
        if isinstance(value, str):
            print(f"  - {key}: {len(value)} chars")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    # 检查messages中的分析师标识
    messages = report.get("messages", [])
    print(f"\n📨 Messages count: {len(messages)}")
    
    # 统计不同分析师的消息
    analyst_msgs = {}
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get('content', '')
            if isinstance(content, str):
                # 检查内容中的分析师标识
                if 'market analyst' in content.lower() or '市场分析师' in content or '技术面分析' in content:
                    analyst_msgs['market'] = analyst_msgs.get('market', 0) + 1
                if 'fundamentals analyst' in content.lower() or '基本面分析师' in content or '基本面分析' in content:
                    analyst_msgs['fundamentals'] = analyst_msgs.get('fundamentals', 0) + 1
                if 'sentiment analyst' in content.lower() or '情绪分析师' in content or '市场情绪分析' in content:
                    analyst_msgs['sentiment'] = analyst_msgs.get('sentiment', 0) + 1
                if 'news analyst' in content.lower() or '新闻分析师' in content or '新闻事件分析' in content:
                    analyst_msgs['news'] = analyst_msgs.get('news', 0) + 1
    
    print(f"\n📈 Analyst messages count:")
    for analyst, count in analyst_msgs.items():
        print(f"  - {analyst}: {count} messages")
    
    client.close()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
